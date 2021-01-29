import numpy as np
import pandas as pd
import wandb

from .utils import image


def iou_from_output(prediction, annotate):
  """Calculates the intersection over union (IoU) metric
  for two mask arrays with entries in 0-255.
  
  Parameters:
    prediction: np.uint8 array
      Predicted mask for image as integer array, values from 0 to 255
    annotate: np.uint8 array
      Ground truth mask as integer array, values 0 and 255.
    
  Returns:
    iou_score: float
      Ratio of the intersection of provided masks
      to the union of the provided masks,
      unless both are empty, in which case -1.0.
  """
  pred_binary, annotate_binary = to_binary(prediction), to_binary(annotate)
  iou_score = binary_iou(pred_binary, annotate_binary)
  return iou_score


def binary_iou(pred_binary, annotate_binary):
    """Calculates the ratio of the pixel count in the intersection
    to the pixel count in the union of two integer arrays
    containing only 0s and 1s, pred_binary and annotate_binary.

  Parameters:
    prediction: np.float array
      Predicted mask for image as float array of 0s and 1s
    annotate: np.float array
      Ground truth mask as float array of 0s and 1s

    Returns:
      iou_score: float
        Ratio of the intersection of provided masks
        to the union of the provided masks,
        unless both are empty, in which case -1.0.
    """
    intersection = pred_binary * annotate_binary
    union = pred_binary + annotate_binary - (intersection)

    intersection_size = intersection.sum()
    union_size = union.sum()

    iou = -1.
    if union_size != 0:
        iou = np.divide(intersection_size, union_size)
    return iou


def to_binary(output):
  return np.round(output / 255.)


def run_evaluation(output_paths, annotation_paths, max_index=None):
  """Evaluates the perfomance of a model by comparing output to ground truth annotations
  based on paths to image files.

  Parameters:
    output_paths: pd.Series
      Contains strings with paths to model outputs as png files
    annotation_paths: pd.Series
      Contains strings with paths to ground truth annotations as png files,
      or nulls where output and annotation don't align
    max_index: int or None
      Maximum index to range over in paths.
      Used for debugging purposes.

  Returns:
    evaluation: list[wandb.Image, wandb.Image, float]
      The first Image is the model output, the second is the ground truth
    metrics: dict[string: numeric or wandb.Media]
      Metrics from evaluation to log to Weights & Biases
  """

  max_index = max_index or len(annotation_paths) - 1

  evaluation = []
  for ii in range(max_index + 1):
    output_path, annotation_path = output_paths.iloc[ii], annotation_paths.iloc[ii]

    if pd.isna(output_path):
      continue

    model_outputs = image.load_to_array(output_path)
    target = image.load_to_array(target_path)
  
    iou_score = iou_from_output(model_outputs, target)
  
    model_outputs_im = wandb.Image(model_outputs, "model output")
    target_im = wandb.Image(target, "target")
  
    evaluation.append([model_outputs, target, float(iou_score)])

  metrics = extract_metrics(evaluation)

  return evaluation, metrics


def extract_metrics(evaluation):
  mean_iou = np.mean([row[-1] for row in evaluation
                      if row[-1] > -1.])

  return {"segmentation_metric": mean_iou,
          "mean_iou": mean_iou}
          
          
def name_submission(result_name, suffix=""):
  name = "".join(result_name.split(":")[:-1])
  name += "-submission"
  if suffix != "":
    name += "-" + "suffix"
  return name

  
def build_table(evaluation):
  evaluation_table = wandb.Table(columns=["out", "target", "iou_score"])
  for row in evaluation:
    evaluation_table.add_data(*row)
  return evaluation_table