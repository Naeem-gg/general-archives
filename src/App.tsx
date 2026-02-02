import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  Archive,
  Check,
  ChevronRight,
  Download,
  MoreVertical,
  RefreshCcw,
  Upload
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";

import DeveloperOptions from "./components/DeveloperOprions";
import { Search } from "./components/Search";
import SinglePaletteArchives from "./components/SinglePaletteArchives";
import { ZoneReorderDialog } from "./components/ZoneReorderDialog";
import { useArchiveStore, useLanguageStore, useSinglePaletteStore, useSortingConfigStore, useToastStore } from "./hooks/store";
import { readConfig } from "./lib/readConfig";
import { save } from "@tauri-apps/plugin-dialog";
import { writeTextFile } from "@tauri-apps/plugin-fs";

interface Content {
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
}

interface ZoneItem {
  position: number;
  content: Content;
}

interface Subzone {
  zone_id: number;
  zone: Zone;
}

interface Zone {
  phase: number;
  zone_items: ZoneItem[];
  subzones: Subzone[];
}

export interface ZoneData {
  zone_id: number;
  zone: Zone;
}

const ZONE_ORDER_STORAGE_KEY = "zoneOrder";

export default function ArchivesDashboard() {
  const fetchArchives = useArchiveStore((state) => state.fetchArchives);
  const { archives, error, isLoading } = useArchiveStore();
  const { singlePaletteZoneIDs, fetchSinglePallets } = useSinglePaletteStore();
  const [showRefreshAnimation, setShowRefreshAnimation] = useState(false);
  const [showReorderDialog, setShowReorderDialog] = useState(false);
  const [zoneOrder, setZoneOrder] = useState<number[]>([]);
  const language = useLanguageStore((state) => state.language);
  const setLanguage = useLanguageStore((state) => state.setLanguage);
  const sortingConfig = useSortingConfigStore();
  const { setShowSuccessToast, setShowErrorToast, setToastMessage, showSuccessToast, showErrorToast, toastMessage } = useToastStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleRefresh = () => {
    setShowRefreshAnimation(true);
    fetchArchives().finally(() => {
      setTimeout(() => setShowRefreshAnimation(false), 1000);
    });
  };

  const handleExportConfig = async () => {
    try {
      const config = {
        version: "1.0",
        exportDate: new Date().toISOString(),
        sortingConfig: {
          rows: sortingConfig.rows,
          columns: sortingConfig.columns,
          corner: sortingConfig.corner,
          direction: sortingConfig.direction,
          isActive: sortingConfig.isActive,
        },
        zoneOrder: zoneOrder,
        language: language,
        singlePaletteZoneIDs: singlePaletteZoneIDs,
      };

      const fileName = `brilon-archiv-config-${new Date().toISOString().split("T")[0]}.json`;
      
      // Use Tauri's save dialog to get the file path
      const filePath = await save({
        defaultPath: fileName,
        filters: [{
          name: "JSON",
          extensions: ["json"]
        }]
      });

      if (!filePath) {
        // User cancelled the dialog
        return;
      }

      // Write the file using Tauri's file system API
      await writeTextFile(filePath, JSON.stringify(config, null, 2));

      setToastMessage(`Konfiguration erfolgreich exportiert: ${filePath}`);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 5000);
    } catch (error) {
      console.error("Error exporting config:", error);
      const errorMessage = error instanceof Error ? error.message : "Unbekannter Fehler";
      setToastMessage(`Fehler beim Exportieren: ${errorMessage}`);
      setShowErrorToast(true);
      setTimeout(() => setShowErrorToast(false), 4000);
    }
  };

  const handleImportConfig = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const config = JSON.parse(text);

      // Validate config structure
      if (!config || typeof config !== "object") {
        throw new Error("Ungültige Konfigurationsdatei");
      }

      // Restore sorting config
      if (config.sortingConfig) {
        sortingConfig.setSortingConfig({
          rows: config.sortingConfig.rows || 0,
          columns: config.sortingConfig.columns || 0,
          corner: config.sortingConfig.corner || 1,
          direction: config.sortingConfig.direction || 1,
        });
      }

      // Restore zone order
      if (Array.isArray(config.zoneOrder)) {
        setZoneOrder(config.zoneOrder);
        localStorage.setItem(ZONE_ORDER_STORAGE_KEY, JSON.stringify(config.zoneOrder));
      }

      // Restore language
      if (typeof config.language === "boolean") {
        setLanguage(config.language);
      }

      // Note: singlePaletteZoneIDs is fetched from server, so we don't restore it

      setToastMessage("Konfiguration erfolgreich importiert");
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 4000);

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("Error importing config:", error);
      const errorMessage = error instanceof Error ? error.message : "Unbekannter Fehler";
      setToastMessage(`Fehler beim Importieren: ${errorMessage}`);
      setShowErrorToast(true);
      setTimeout(() => setShowErrorToast(false), 4000);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  useEffect(() => {
    fetchArchives();
    fetchSinglePallets();
  }, [fetchArchives, fetchSinglePallets]);

  // Load zone order from localStorage
  useEffect(() => {
    const savedOrder = localStorage.getItem(ZONE_ORDER_STORAGE_KEY);
    if (savedOrder) {
      try {
        setZoneOrder(JSON.parse(savedOrder));
      } catch (e) {
        console.error("Failed to parse zone order from localStorage", e);
      }
    }
  }, []);

  // Get zones list for reordering
  const zonesForReorder = useMemo(() => {
    return archives
      .filter((archive) => {
        const zoneName = (archive.zone as any).zone_name
        if (!zoneName) return false;
        if (singlePaletteZoneIDs.includes(archive.zone_id)) return false;
        return true;
      })
      .map((archive) => ({
        zone_id: archive.zone_id,
        zone_name: (archive.zone as any).zone_name,
      }));
  }, [archives]);

  // Handle zone reorder
  const handleZoneReorder = (reorderedZones: { zone_id: number; zone_name: string }[]) => {
    const newOrder = reorderedZones.map((z) => z.zone_id);
    setZoneOrder(newOrder);
    localStorage.setItem(ZONE_ORDER_STORAGE_KEY, JSON.stringify(newOrder));
  };

  // Get sorted archives based on zone order
  const sortedArchives = useMemo(() => {
    if (zoneOrder.length === 0) {
      return archives;
    }

    const orderMap = new Map(zoneOrder.map((id, index) => [id, index]));
    const sorted = [...archives].sort((a, b) => {
      const aIndex = orderMap.get(a.zone_id);
      const bIndex = orderMap.get(b.zone_id);

      // If both are in the order, sort by their position
      if (aIndex !== undefined && bIndex !== undefined) {
        return aIndex - bIndex;
      }
      // If only a is in the order, a comes first
      if (aIndex !== undefined) return -1;
      // If only b is in the order, b comes first
      if (bIndex !== undefined) return 1;
      // If neither is in the order, maintain original order
      return 0;
    });

    return sorted;
  }, [archives, zoneOrder]);
  const [developerOptions, setDeveloperOptions] = useState<string>("");
  useEffect(() => {
    const getDev = async () => {
      const config = await readConfig();
      setDeveloperOptions(config.devOptions);
    };
    getDev();
  }, []);
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 260,
        damping: 20,
      },
    },
  };
  const renderArchiveCards = () => {
    if (error) {
      return (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full"
        >
          <Alert
            variant="destructive"
            className="backdrop-blur-sm bg-destructive/90 border border-destructive/20 shadow-lg text-white"
          >
            <AlertCircle className="h-5 w-5" color="white" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </motion.div>
      );
    }

    if (isLoading) {
      return (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {[...Array(8)].map((_, i) => (
            <motion.div key={i} variants={itemVariants as any}>
              <Card className="overflow-hidden border border-border/50 bg-card/30 backdrop-blur-sm">
                <CardHeader className="border-b p-6 bg-gradient-to-r from-muted/80 to-muted/30">
                  <Skeleton className="h-6 w-2/3" />
                </CardHeader>
                <CardContent className="p-6 space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      );
    }

    return (
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      >
        {sortedArchives.map((archive) => {
          const zoneName = archive.zone.zone_name;
          if (!zoneName) return null;
          if (
            singlePaletteZoneIDs.includes(archive.zone_id)
          )
            return null; // Skip these archives as they are handled separately
          return (
            <motion.div key={archive.zone_id} variants={itemVariants as any}>
              <Link to={`/details/${archive.zone_id}`} className="block h-full">
                <Card className="group h-full overflow-hidden border border-border/50 bg-card/30 backdrop-blur-sm transition-all duration-300 hover:bg-card/80 hover:shadow-lg hover:shadow-primary/5 dark:hover:shadow-primary/10">
                  <CardHeader className="border-b p-6 bg-gradient-to-r from-muted/80 to-muted/30 transition-colors duration-300 group-hover:from-primary/10 group-hover:to-primary/5">
                    <CardTitle className="flex items-center text-xl">
                      <div className="mr-3 flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary transition-transform duration-300 group-hover:scale-110">
                        <Archive className="h-4 w-4" />
                      </div>
                      <span className="transition-colors duration-300 group-hover:text-primary">
                        {zoneName}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <CardDescription className="text-sm font-medium dark:text-white">
                          <span className="text-muted-foreground">
                            {language ? "Palette" : "Rack"}:
                          </span>{" "}
                          {archive.zone.subzones.length}
                        </CardDescription>
                        <Badge
                          variant="outline"
                          className="bg-background/50 transition-colors duration-300 group-hover:bg-primary/10 group-hover:text-primary"
                        >
                          {language ? "Aktiv" : "Active"}
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="text-xs text-muted-foreground">
                          {language ? "Proben je Palette" : "Tubes per Rack "}:
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {archive.zone.subzones.map((subzone, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className="transition-all duration-300 group-hover:bg-primary/20"
                            >
                              {subzone.zone.zone_items.length ?? "0"}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center justify-end text-xs text-muted-foreground">
                        <span className="mr-1">
                          {language ? "Details anzeigen" : "View Details"}
                        </span>
                        <ChevronRight className="h-3 w-3 transition-transform duration-300 group-hover:translate-x-1" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          );
        })}
        <SinglePaletteArchives zoneIDs={singlePaletteZoneIDs} archives={archives} />
      </motion.div>
    );
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-background to-background/80">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.02] pointer-events-none"></div>

      <div className="container relative mx-auto p-6 lg:p-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="flex flex-col space-y-6 md:flex-row md:items-center md:justify-between md:space-y-0">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
                <span className="bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                  Brilon Archiv
                </span>
              </h1>
              <p className="text-sm text-muted-foreground">
                Ihre Übersicht über alle Archivpositionen und archivierte Proben
              </p>
              <div className="flex items-center space-x-2">
                {developerOptions === "Naeem" && <DeveloperOptions />}

                <motion.div
                  animate={
                    showRefreshAnimation ? { rotate: 360 } : { rotate: 0 }
                  }
                  transition={{ duration: 1, ease: "easeInOut" }}
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1"
                    onClick={handleRefresh}
                  >
                    <RefreshCcw className="h-3.5 w-3.5" />
                    <span className="text-xs">Aktualisieren</span>
                  </Button>
                  
                </motion.div>
              </div>
            </div>

            <div className="flex flex-col space-y-3 sm:flex-row sm:items-center sm:space-x-4 sm:space-y-0">
              <Search />
              <Button
                variant="outline"
                size="sm"
                className="h-9 gap-2"
                onClick={handleExportConfig}
                title="Export Configuration"
              >
                <Download className="h-4 w-4" />
                <span className="text-xs">Export</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-9 gap-2"
                onClick={handleImportConfig}
                title="Import Configuration"
              >
                <Upload className="h-4 w-4" />
                <span className="text-xs">Import</span>
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleFileChange}
              />
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9"
                onClick={() => setShowReorderDialog(true)}
                title="Reorder Zones"
              >
                <MoreVertical className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        ></motion.div>

        <ScrollArea className="h-[calc(100vh-220px)]">
          <AnimatePresence mode="wait">{renderArchiveCards()}</AnimatePresence>
        </ScrollArea>
      </div>

      <ZoneReorderDialog
        open={showReorderDialog}
        onOpenChange={setShowReorderDialog}
        zones={zonesForReorder}
        onReorder={handleZoneReorder}
      />

      {/* Success Toast */}
      <AnimatePresence>
        {showSuccessToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-4 right-4 z-50"
          >
            <div className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-3 text-white shadow-lg max-w-md">
              <Check className="h-5 w-5 flex-shrink-0" />
              <span className="text-sm">{toastMessage}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Toast */}
      <AnimatePresence>
        {showErrorToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-4 right-4 z-50"
          >
            <div className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-3 text-white shadow-lg max-w-md">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span className="text-sm">{toastMessage}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
