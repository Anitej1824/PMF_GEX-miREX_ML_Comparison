"""
Utility functions for training and evaluating machine-learning models.

This module contains reusable functions for evaluating classification models using cross-validation and multiple performance metrics.
"""

from sklearn.model_selection import cross_validate
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

def evaluate_model(model, X, y, model_name, data_type, cv):
    """
    Evaluate a classification model using cross-validation.

    The model is evaluated using multiple classification metrics across
    the supplied cross-validation folds. Only test-fold performance is
    recorded to avoid reporting training performance.

    Parameters
    ----------
    model : estimator
        Scikit-learn compatible classification estimator implementing
        ``fit`` and ``predict_proba`` or ``decision_function``.

    X : array-like
        Feature matrix containing samples as rows and features as columns.

    y : array-like
        Target labels corresponding to the samples in ``X``.

    model_name : str
        Name used to identify the model in the returned results.

    data_type : str
        Name of the dataset being evaluated, for example ``"Gene"``
        or ``"miRNA"``.

    cv : cross-validation splitter
        Scikit-learn cross-validation strategy used to generate training
        and validation folds.

    Returns
    -------
    dict
        Dictionary containing the dataset and model identifiers together
        with the mean and standard deviation of ROC-AUC and accuracy,
        and the mean precision, recall, and F1 score across folds.

    Notes
    -----
    The function evaluates the following metrics:

    - ROC-AUC
    - Accuracy
    - Precision
    - Recall
    - F1 score

    Training-fold performance is excluded by setting
    ``return_train_score=False``.
    """

    scoring = {
        "roc_auc": "roc_auc",
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1"
    }

    cv_results = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=scoring,
        return_train_score=False
    )

    result = {
        "Dataset": data_type,
        "Model": model_name,
        "ROC_AUC_mean": cv_results["test_roc_auc"].mean(),
        "ROC_AUC_std": cv_results["test_roc_auc"].std(),
        "Accuracy_mean": cv_results["test_accuracy"].mean(),
        "Accuracy_std": cv_results["test_accuracy"].std(),
        "Precision_mean": cv_results["test_precision"].mean(),
        "Recall_mean": cv_results["test_recall"].mean(),
        "F1_mean": cv_results["test_f1"].mean()
    }

    return result

def create_pipelines(k):
    """
    Create Logistic Regression and Random Forest pipelines
    using the specified number of selected features.

    Feature selection is performed inside each pipeline so that
    feature selection occurs independently within each CV training fold.
    """

    logreg_pipeline = Pipeline([
        ("feature_selection", SelectKBest(score_func=f_classif, k=k)),
        ("scaling", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=2000))
    ])

    rf_pipeline = Pipeline([
        ("feature_selection", SelectKBest(score_func=f_classif, k=k)),
        ("classifier", RandomForestClassifier(
            n_estimators=500,
            random_state=42
        ))
    ])

    return logreg_pipeline, rf_pipeline