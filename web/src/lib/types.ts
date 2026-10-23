export type Prediction = {
  verdict: "scam" | "genuine";
  scam_probability: number;
  scam_type?: string;
  scam_type_guess?: string;
  scam_type_confidence?: number;
  signals?: string[];
};

export type Health = {
  status: string;
  thresholds: { balanced: number; strict: number };
  evaluation?: { scam_templates_caught: number; genuine_templates_left_alone: number; roc_auc: number };
};

export type Entry = {
  id: number;
  text: string;
  p: number;
  band: BandName;
  flagged: boolean;
  type: string | null;
  at: number;
};

export type BandName = "Low" | "Medium" | "High" | "Very high";
