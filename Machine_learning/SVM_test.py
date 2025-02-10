#!/usr/bin/env python
# svm_cv_pipeline.py
"""
Demonstration of an EEG classification pipeline using SVM
with k-fold cross-validation for each subject.
"""

import numpy as np
import matplotlib.pyplot as plt
import mne

from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

##############################################################################
#                      CONFIG AND PATHS
##############################################################################

SUBJECT_FILES = {
    '9':  r"C:\Users\anjaz\OneDrive\Desktop\preprocessed_ICA_eksperiment_annotated_9.set",
    # Add more subjects as needed...
}

STANDARD_64_LABELS = [
    'Fp1','Fz','F3','F7','FT9','FC5','FC1','C3','T7','TP9','CP5','CP1',
    'Pz','P3','P7','O1','Oz','O2','P4','P8','TP10','CP6','CP2','Cz','C4',
    'T8','FT10','FC6','FC2','F4','F8','Fp2','AF7','AF3','AFz','F1','F5',
    'FT7','FC3','C1','C5','TP7','CP3','P1','P5','PO7','PO3','POz','PO4',
    'PO8','P6','P2','CPz','CP4','TP8','C6','C2','FC4','FT8','F6','AF8',
    'AF4','F2','FCz'
]

EVENT_ID_MAP = {'11': 11, '12': 12}  # EEG event codes
LABEL_MAPPING = {'11': 0, '12': 1}   # Map event to class ID

TMIN = -0.2
TMAX = 0.8

SAVE_FIGURES = False  # set True to save .png figures

##############################################################################
#                           DATA LOADING
##############################################################################

def load_and_extract_erps(eeg_data_path, channel_labels_64,
                          event_id_map, tmin, tmax, preload=True):
    """
    Load an EEGLAB .set file, reorder channels to match 64-channel standard,
    then epoch using event_id_map. Return (X, y, info).
    X: (n_epochs, n_channels, n_times)
    y: array of integer labels
    """
    raw = mne.io.read_raw_eeglab(eeg_data_path, preload=preload)
    eeg_ch_names = raw.copy().pick_types(eeg=True).ch_names
    raw_eeg_data = raw.get_data(picks=eeg_ch_names).T  # shape: (time, channels)

    n_samples, _ = raw_eeg_data.shape
    reordered_eeg_data = np.zeros((n_samples, 64), dtype=np.float32)

    # Reorder channels
    for idx, ch_label in enumerate(channel_labels_64):
        if ch_label in eeg_ch_names:
            ch_idx = eeg_ch_names.index(ch_label)
            reordered_eeg_data[:, idx] = raw_eeg_data[:, ch_idx]

    sfreq = raw.info['sfreq']
    new_info = mne.create_info(ch_names=channel_labels_64, sfreq=sfreq, ch_types='eeg')
    reordered_raw = mne.io.RawArray(reordered_eeg_data.T, new_info)

    # Create epochs
    events, found_event_id = mne.events_from_annotations(raw)
    real_event_id = {}
    for desc, code in event_id_map.items():
        if desc in found_event_id:
            real_event_id[desc] = code

    epochs = mne.Epochs(
        reordered_raw, events=events, event_id=real_event_id,
        tmin=tmin, tmax=tmax, baseline=None, preload=True
    )
    X = epochs.get_data()  # shape: (n_epochs, 64, n_times)
    y = epochs.events[:, 2]
    info = epochs.info

    return X, y, info

##############################################################################
#                              PLOTTING
##############################################################################

def plot_confusion_matrix(cm, subj_id, class_names=("Class0","Class1"), title_suffix=""):
    """
    Plot a confusion matrix.
    """
    plt.figure(figsize=(4,4))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title(f"Subject {subj_id} - Confusion Matrix {title_suffix}")
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, f"{cm[i,j]}",
                     ha="center", va="center",
                     color="white" if cm[i,j] > thresh else "black")
    
    plt.tight_layout()
    plt.ylabel("True")
    plt.xlabel("Predicted")
    if SAVE_FIGURES:
        fname = f"Subject_{subj_id}_confusion_matrix{title_suffix}.png"
        plt.savefig(fname)
        print(f"Saved figure to {fname}")
    plt.show()

##############################################################################
#                                   MAIN
##############################################################################

def main():
    subject_ids = list(SUBJECT_FILES.keys())

    # Store final results for all subjects
    all_subject_results = {}

    # CV settings
    cv_splits = 5  # 5-fold cross-validation
    skf = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=42)

    # Define pipeline and param grid
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('svc', SVC())
    ])
    param_grid = {
        'svc__C': [0.1, 1, 10],
        'svc__kernel': ['linear', 'rbf']
        # you can add more SVM params here
    }

    # ========== PROCESS EACH SUBJECT WITH K-FOLD CV ==========
    for subj_id in subject_ids:
        print(f"\nProcessing Subject {subj_id}...")
        eeg_path = SUBJECT_FILES[subj_id]

        # 1) Load data
        X, y, info = load_and_extract_erps(
            eeg_data_path=eeg_path,
            channel_labels_64=STANDARD_64_LABELS,
            event_id_map=EVENT_ID_MAP,
            tmin=TMIN, tmax=TMAX
        )

        # 2) Flatten (n_epochs, n_channels, n_times) -> (n_epochs, features)
        n_epochs, n_channels, n_times = X.shape
        X_2d = X.reshape(n_epochs, -1)

        # 3) Grid Search with cross-validation
        grid_search = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            scoring='accuracy',
            n_jobs=-1,
            cv=skf
        )
        grid_search.fit(X_2d, y)

        # Best average CV accuracy across folds
        best_score = grid_search.best_score_
        best_params = grid_search.best_params_

        # 4) Evaluate with cross_val_predict to get predictions for each fold
        #    using the best parameters found.
        best_pipeline = grid_search.best_estimator_
        y_pred_cv = cross_val_predict(best_pipeline, X_2d, y, cv=skf)

        cv_acc = accuracy_score(y, y_pred_cv)
        cm = confusion_matrix(y, y_pred_cv)
        cr = classification_report(y, y_pred_cv)

        # Store results
        all_subject_results[subj_id] = {
            'best_params': best_params,
            'cv_score': best_score,
            'cv_acc': cv_acc,
            'conf_mat': cm,
            'clf_report': cr
        }

    # ========== FINAL REPORT ==========
    print("\n\n==== FINAL CROSS-VALIDATION RESULTS ====\n")
    for subj_id, res in all_subject_results.items():
        print("-"*50)
        print(f"Subject {subj_id} Results:")
        print(f"  Best Params from GridSearch: {res['best_params']}")
        print(f"  Mean CV Accuracy (GridSearch Best Score): {res['cv_score']:.3f}")
        print(f"  CV Accuracy (via cross_val_predict): {res['cv_acc']:.3f}")
        print("  Confusion Matrix (pooled across folds):\n", res['conf_mat'])
        print("  Classification Report:\n", res['clf_report'])

    # Optional confusion matrix plots
    for subj_id, res in all_subject_results.items():
        plot_confusion_matrix(
            cm=res['conf_mat'],
            subj_id=subj_id,
            class_names=["Class0","Class1"],
            title_suffix="(CV Prediction)"
        )

if __name__ == "__main__":
    main()