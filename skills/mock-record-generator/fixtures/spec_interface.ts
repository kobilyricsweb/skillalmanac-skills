// Fixture: four-field interface for the offline smoke run.
export interface Account {
  id: string;
  balance: number;
  active: boolean;
  tier?: "basic" | "plus";
}
