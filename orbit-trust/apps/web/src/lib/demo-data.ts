export type Urgency = "P0" | "P1" | "P2" | "P3";
export type EvidenceState = "Incomplete" | "Conflicting" | "Usable" | "Unsupported";

export interface ReviewCase {
  id: string;
  urgency: Urgency;
  primary: string;
  secondary: string;
  catalogIds: string;
  deadline: string;
  slack: string;
  pc: string;
  evidence: EvidenceState;
  reason: string;
  analyst: string;
  stage: string;
}

export const reviewCases: ReviewCase[] = [
  {
    id: "OT-0911-014",
    urgency: "P0",
    primary: "ASTERIA-3",
    secondary: "COSMOS 2251 DEB",
    catalogIds: "58422 / 34454",
    deadline: "12 Sep · 09:42 IST",
    slack: "Overdue 08m",
    pc: "2.73 × 10⁻³",
    evidence: "Incomplete",
    reason: "Covariance age exceeds policy; command window closing",
    analyst: "A. Rao",
    stage: "Review now",
  },
  {
    id: "OT-0911-009",
    urgency: "P1",
    primary: "KALPANA-X",
    secondary: "SL-8 R/B",
    catalogIds: "60218 / 12988",
    deadline: "12 Sep · 10:35 IST",
    slack: "45m",
    pc: "8.41 × 10⁻⁴",
    evidence: "Conflicting",
    reason: "Two provider updates disagree on miss distance",
    analyst: "Unassigned",
    stage: "Evidence check",
  },
  {
    id: "OT-0911-021",
    urgency: "P1",
    primary: "VARUNA-2",
    secondary: "OBJECT 56712",
    catalogIds: "59103 / 56712",
    deadline: "Not supplied",
    slack: "Unknown",
    pc: "1.12 × 10⁻⁴",
    evidence: "Incomplete",
    reason: "Review deadline and maneuver context missing",
    analyst: "M. Chen",
    stage: "Awaiting data",
  },
  {
    id: "OT-0910-087",
    urgency: "P2",
    primary: "PRITHVI-7",
    secondary: "FENGYUN 1C DEB",
    catalogIds: "57431 / 31126",
    deadline: "12 Sep · 15:20 IST",
    slack: "5h 30m",
    pc: "4.08 × 10⁻⁵",
    evidence: "Usable",
    reason: "Stable estimate; acknowledgement still pending",
    analyst: "S. Iyer",
    stage: "Analysis ready",
  },
  {
    id: "OT-0910-061",
    urgency: "P3",
    primary: "OCEANWATCH-1",
    secondary: "CZ-4B DEB",
    catalogIds: "55390 / 43821",
    deadline: "13 Sep · 03:10 IST",
    slack: "17h 20m",
    pc: "3.59 × 10⁻¹⁰",
    evidence: "Usable",
    reason: "Below demo threshold; continue monitoring updates",
    analyst: "A. Rao",
    stage: "Monitoring",
  },
];

export const evidenceChecks = [
  { label: "State vectors", state: "pass", detail: "Both objects supplied in synthetic inertial frame." },
  { label: "Covariance", state: "fail", detail: "Primary covariance is 19h old; policy limit is 12h." },
  { label: "Frame and epoch", state: "pass", detail: "Frames match and epochs are within 0.4 seconds." },
  { label: "Maneuver context", state: "warn", detail: "Secondary-object maneuver status was not supplied." },
];

export const fleetRows = [
  { pair: "ASTERIA-3 ↔ COSMOS DEB", baseline: "2.73 × 10⁻³", one: "3.59 × 10⁻¹⁰", two: "3.59 × 10⁻¹⁰", baselineState: "bad", oneState: "good", twoState: "good" },
  { pair: "ASTERIA-3 ↔ VARUNA-2", baseline: "3.40 × 10⁻¹⁶", one: "1.98 × 10⁻²", two: "2.04 × 10⁻³³", baselineState: "good", oneState: "bad", twoState: "good" },
  { pair: "COSMOS DEB ↔ VARUNA-2", baseline: "3.59 × 10⁻¹⁰", one: "3.59 × 10⁻¹⁰", two: "3.59 × 10⁻¹⁰", baselineState: "good", oneState: "good", twoState: "good" },
];

export const activityItems = [
  { time: "09:51:08", title: "Assessment reopened", detail: "Material provider revision r18 received", kind: "alert" },
  { time: "09:50:43", title: "Evidence audit completed", detail: "4 checks · 1 failed · 1 incomplete", kind: "calc" },
  { time: "09:50:42", title: "Encounter calculation completed", detail: "orbit-core linear-gaussian-2d · 18 ms", kind: "calc" },
  { time: "09:49:12", title: "Report revision imported", detail: "Space-Track CDM · source revision r18", kind: "data" },
  { time: "09:42:00", title: "Review deadline passed", detail: "Unacknowledged urgency floor raised to P0", kind: "alert" },
];
