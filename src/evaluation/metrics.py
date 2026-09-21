from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, matthews_corrcoef, precision_score, recall_score, roc_auc_score


def binary_metrics(y_true, y_pred, y_score=None) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": accuracy_score(y_true, y_pred), "precision": precision_score(y_true, y_pred, zero_division=0),
        "attack_recall": recall_score(y_true, y_pred, zero_division=0), "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_score) if y_score is not None else None,
        "pr_auc": average_precision_score(y_true, y_score) if y_score is not None else None,
        "mcc": matthews_corrcoef(y_true, y_pred),
        "specificity": tn / (tn + fp) if tn + fp else 0.0,
        "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn),
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "false_negative_rate": fn / (fn + tp) if fn + tp else 0.0,
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }
