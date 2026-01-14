export interface Tube {
  position: number;
  content: {
    color: string;
    fluid_level: number;
    line_code: string;
    type: string;
    added_time: string; // ISO date string
  };
}

export interface ZoneItem {
  position: number;
  content: {
    line_code: string;
    color: number;
    type: number;
    current_zone_id: number;
    current_subzone_id: number;
    next_zone_id: number | null;
    fluid_level: number;
    transits: string[];
    centrifuged: boolean;
    decapped: boolean;
  };
}

export interface Zone {
  phase: number;
  zone_items: ZoneItem[];
  subzones: any[];
}
