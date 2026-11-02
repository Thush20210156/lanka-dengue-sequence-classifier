"""Group-separated QDA experiment with frozen test evaluation and post-hoc XAI."""
from pathlib import Path
import json,warnings,hashlib,platform
import numpy as np
import pandas as pd
import joblib,sklearn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler,label_binarize
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import StratifiedGroupKFold,GridSearchCV
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,classification_report,confusion_matrix,ConfusionMatrixDisplay,roc_auc_score,RocCurveDisplay
from sklearn.inspection import permutation_importance,PartialDependenceDisplay
from features import FEATURES
ROOT=Path(__file__).resolve().parent
LABELS=['DENV-1','DENV-2','DENV-3','DENV-4']
def metrics(model,X,y):
    pred=model.predict(X);prob=model.predict_proba(X)
    return {'accuracy':accuracy_score(y,pred),'balanced_accuracy':balanced_accuracy_score(y,pred),'macro_f1':f1_score(y,pred,labels=LABELS,average='macro',zero_division=0),'weighted_f1':f1_score(y,pred,average='weighted',zero_division=0),'macro_ovr_auc':roc_auc_score(y,prob,labels=LABELS,multi_class='ovr',average='macro')}
def main():
    out=ROOT/'results';out.mkdir(exist_ok=True)
    df=pd.read_csv(ROOT/'data/sri_lanka_dengue_features.csv');X=df[FEATURES];y=df.serotype;groups=df.group_id
    dev,test=next(StratifiedGroupKFold(5,shuffle=True,random_state=42).split(X,y,groups))
    tr,va=next(StratifiedGroupKFold(4,shuffle=True,random_state=43).split(X.iloc[dev],y.iloc[dev],groups.iloc[dev]))
    train,val=dev[tr],dev[va]
    splits={k:df.iloc[ix].accession.tolist() for k,ix in [('train',train),('validation',val),('test',test)]}
    (out/'split_accessions.json').write_text(json.dumps(splits,indent=2))
    for a,b in [(train,val),(train,test),(val,test)]:assert not set(groups.iloc[a])&set(groups.iloc[b])
    pipe=Pipeline([('variance',VarianceThreshold()),('scale',StandardScaler()),('qda',QuadraticDiscriminantAnalysis())])
    cv=StratifiedGroupKFold(3,shuffle=True,random_state=44)
    search=GridSearchCV(pipe,{'qda__reg_param':[.05,.1,.25,.5,.75,1.]},scoring='f1_macro',cv=cv,n_jobs=1,error_score='raise')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');search.fit(X.iloc[train],y.iloc[train],groups=groups.iloc[train]);model=search.best_estimator_
        vm=metrics(model,X.iloc[val],y.iloc[val]);model.fit(X.iloc[dev],y.iloc[dev])
    joblib.dump(model,out/'model.joblib')
    cvtable=pd.DataFrame({'regularization':search.cv_results_['param_qda__reg_param'].astype(float),'mean_cv_macro_f1':search.cv_results_['mean_test_score'],'std_cv_macro_f1':search.cv_results_['std_test_score']});cvtable.to_csv(out/'cv_results.csv',index=False)
    tm=metrics(model,X.iloc[test],y.iloc[test]);baseline=DummyClassifier(strategy='prior').fit(X.iloc[dev],y.iloc[dev]);bm=metrics(baseline,X.iloc[test],y.iloc[test])
    pred=model.predict(X.iloc[test]);prob=model.predict_proba(X.iloc[test]);cm=confusion_matrix(y.iloc[test],pred,labels=LABELS)
    report=pd.DataFrame(classification_report(y.iloc[test],pred,labels=LABELS,output_dict=True,zero_division=0)).T;report.to_csv(out/'classification_report.csv')
    preds=df.iloc[test][['accession','serotype','group_id']].copy();preds['predicted']=pred
    for i,c in enumerate(model.classes_):preds['prob_'+c]=prob[:,i]
    preds.to_csv(out/'test_predictions.csv',index=False)
    fig,ax=plt.subplots(figsize=(6,4));ConfusionMatrixDisplay(cm,display_labels=LABELS).plot(ax=ax,colorbar=False);ax.set_title('Group-separated held-out genomes');fig.tight_layout();fig.savefig(out/'confusion_matrix.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4));biny=label_binarize(y.iloc[test],classes=LABELS)
    for i,c in enumerate(LABELS):RocCurveDisplay.from_predictions(biny[:,i],prob[:,i],name=c,ax=ax)
    ax.plot([0,1],[0,1],'--',color='gray');fig.tight_layout();fig.savefig(out/'roc.png',dpi=180);plt.close(fig)
    imp=permutation_importance(model,X.iloc[test],y.iloc[test],scoring='f1_macro',n_repeats=30,random_state=45)
    importance=pd.DataFrame({'feature':FEATURES,'mean_macro_f1_drop':imp.importances_mean,'shuffle_sd':imp.importances_std}).sort_values('mean_macro_f1_drop',ascending=False);importance.to_csv(out/'permutation_importance.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,5));p=importance.iloc[::-1];ax.barh(p.feature,p.mean_macro_f1_drop,xerr=p.shuffle_sd);ax.set_xlabel('Macro-F1 decrease after shuffling (mean +/- SD)');fig.tight_layout();fig.savefig(out/'importance.png',dpi=180);plt.close(fig)
    top=importance.feature.iloc[:2].tolist();fig,ax=plt.subplots(1,2,figsize=(8,3));PartialDependenceDisplay.from_estimator(model,X.iloc[dev],top,target='DENV-1',ax=ax,method='brute');fig.suptitle('Partial dependence: probability of DENV-1');[a.set_ylim(0,1) for a in ax];fig.tight_layout();fig.savefig(out/'pdp.png',dpi=180);plt.close(fig)
    # Bootstrap whole exact/isolate groups, not individual rows, without refitting.
    rng=np.random.default_rng(46);testgroups=groups.iloc[test].to_numpy();unique=np.unique(testgroups);boot=[];truth=y.iloc[test].to_numpy()
    for _ in range(2000):
        chosen=rng.choice(unique,size=len(unique),replace=True);ix=np.concatenate([np.flatnonzero(testgroups==g) for g in chosen]);boot.append(f1_score(truth[ix],pred[ix],labels=LABELS,average='macro',zero_division=0))
    # Supplementary temporal check. Not used to select model or threshold.
    temporal={};early=df.index[df.collection_year<=2018].to_numpy();late=df.index[df.collection_year>=2019].to_numpy()
    late=late[~groups.iloc[late].isin(set(groups.iloc[early])).to_numpy()]
    temporalmodel=clone(model)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');temporalmodel.fit(X.iloc[early],y.iloc[early]);tp=temporalmodel.predict(X.iloc[late])
    temporal={'train_through_year':2018,'test_from_year':2019,'train_rows':len(early),'test_rows':len(late),'train_class_counts':y.iloc[early].value_counts().to_dict(),'test_class_counts':y.iloc[late].value_counts().to_dict(),'accuracy':accuracy_score(y.iloc[late],tp),'macro_f1_present_classes':f1_score(y.iloc[late],tp,average='macro',zero_division=0),'note':'DENV-4 has no post-2018 observations here; this is not a four-class temporal validation. Missing years omitted. Not used for tuning.'}
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');negative=clone(model).fit(X.iloc[dev],np.random.default_rng(47).permutation(y.iloc[dev].to_numpy()))
    negmetrics=metrics(negative,X.iloc[test],y.iloc[test])
    # Wilson interval for accuracy remains informative when all predictions are correct.
    n=len(test);phat=tm['accuracy'];z=1.959963984540054;den=1+z*z/n;center=(phat+z*z/(2*n))/den;half=z*np.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/den
    joint_rng=np.random.default_rng(48);joint=[]
    for _ in range(30):
        shuffled=X.iloc[test].iloc[joint_rng.permutation(len(test))].copy();shuffled.index=X.iloc[test].index
        joint.append(tm['macro_f1']-f1_score(y.iloc[test],model.predict(shuffled),labels=LABELS,average='macro',zero_division=0))
    meta={'joint_all_descriptors_permutation':{'mean_macro_f1_drop':float(np.mean(joint)),'shuffle_sd':float(np.std(joint)),'repeats':30},'negative_control_test':negmetrics,'accuracy_wilson_95':[center-half,min(1.,center+half)],'dataset_rows':len(df),'dataset_sha256':hashlib.sha256((ROOT/'data/sri_lanka_dengue_features.csv').read_bytes()).hexdigest(),'split_sizes':{k:len(v) for k,v in splits.items()},'split_class_counts':{k:df.set_index('accession').loc[v].serotype.value_counts().to_dict() for k,v in splits.items()},'split_group_counts':{k:int(df.set_index('accession').loc[v].group_id.nunique()) for k,v in splits.items()},'selected_regularization':search.best_params_['qda__reg_param'],'cv_macro_f1':search.best_score_,'validation':vm,'test':tm,'baseline_test':bm,'confusion_matrix':cm.tolist(),'macro_f1_group_bootstrap_95_percentile':np.quantile(boot,[.025,.975]).tolist(),'warning_messages':sorted(set(str(w.message) for w in caught)),'temporal_check':temporal,'python':platform.python_version(),'sklearn':sklearn.__version__}
    (out/'metrics.json').write_text(json.dumps(meta,indent=2))
    X.iloc[dev].agg(['min','max','median']).to_json(out/'development_reference.json')
    print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
