import { deleteArchive, getArchivesData } from "@/lib/xmlrpc";
import { create } from "zustand";
import { Tube } from "../components/types";
export interface Archive {
  zone_id: number;
  zone: {
    phase: number;
    zone_items: any[];
    subzones: any[];
  };
}

interface ArchiveStore {
  archives: Archive[];
  isLoading: boolean;
  setIsLoading: (isLoading: boolean) => void;
  error: string | null;
  // Fetch the archives data from the server
  fetchArchives: () => Promise<void>;
  // Delete archive(s) by barcode and update the store
  deleteArchiveByBarcode: (tubeIds: string[], zoneId: number) => Promise<void>;
}

export const useArchiveStore = create<ArchiveStore>((set) => ({
  archives: [],

  isLoading: false,
  setIsLoading: (isLoading: boolean) => set(() => ({ isLoading })),
  error: null,
  fetchArchives: async () => {
    set({ isLoading: true, error: null });
    try {
      // await restart(false)
      const data = await getArchivesData();
      // data is assumed to be an array of Archive objects
      set({ archives: data });
    } catch (error: any) {
      set({ error: error.message || "Error fetching archives" });
    } finally {
      set({ isLoading: false });
    }
  },
  deleteArchiveByBarcode: async (tubeIds: string[], zoneId: number) => {
    try {
      // Call the XML-RPC deletion method.
      await deleteArchive(tubeIds);
      // Update the store: for example, remove the archive with the matching zone_id.
      // Adjust this logic if you want to only remove specific items.
      set((state) => ({
        archives: state.archives.filter(
          (archive) => archive.zone_id !== zoneId,
        ),
      }));
    } catch (error: any) {
      set({ error: error.message || "Error deleting archive" });
    }
  },
}));

type TubesStore = {
  tubes: Tube[];
  index: number;
  setIndex: (index: number) => void;
  setTubes: (tubes: Tube[]) => void;
  highlightedTube: Tube; // Single highlighted tube
  selectedTubes: Tube[]; // Array of selected tubes
  setHighlightedTube: (tube: Tube) => void; // Function to set the highlighted tube
  setSelectedTubes: (tubes: Tube[]) => void; // Function to set the array of selected tubes
};

export const useTubesStore = create<TubesStore>((set) => ({
  index: 0,
  setIndex: (index: number) => set({ index }),
  tubes: [],
  setTubes: (tubes: Tube[]) => set({ tubes }),
  highlightedTube: {
    index: 0,
    position: 0,
    content: { line_code: "0", fluid_level: 0, type: "", color: "",added_time:"" },
  }, // Initialize as null or a default tube
  selectedTubes: [], // Initialize as an empty array
  setHighlightedTube: (tube) => set(() => ({ highlightedTube: tube })), // Update the highlighted tube
  setSelectedTubes: (tubes) => set(() => ({ selectedTubes: tubes })), // Update the array of selected tubes
}));

type ToastStore = {
  showSuccessToast: boolean;
  setShowSuccessToast: (show: boolean) => void;
  toastMessage: string;
  setToastMessage: (message: string) => void;
};
export const useToastStore = create<ToastStore>((set) => ({
  showSuccessToast: false,
  setShowSuccessToast: (show: boolean) =>
    set(() => ({ showSuccessToast: show })),
  toastMessage: "",
  setToastMessage: (message: string) => set(() => ({ toastMessage: message })),
}));

type LoadingStore = {
  isLoading: boolean;
  setIsLoading: (isLoading: boolean) => void;
};
export const useLoadingStore = create<LoadingStore>((set) => ({
  isLoading: false,
  setIsLoading: (isLoading: boolean) => set(() => ({ isLoading })),
}));

type LanguageStore = {
  language: boolean;
  setLanguage: (language: boolean | ((prev: boolean) => boolean)) => void;
};

export const useLanguageStore = create<LanguageStore>((set) => ({
  language: true,
  setLanguage: (language) =>
    set((state) => ({
      language:
        typeof language === "function" ? language(state.language) : language,
    })),
}));
