"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  RefreshCw,
  Slash,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "./ui/breadcrumb";

import {
  useArchiveStore,
  useLoadingStore,
  useSortingConfigStore,
  useToastStore,
  useTubesStore,
} from "@/hooks/store";
import { deleteArchive } from "@/lib/xmlrpc";
import { ask, message } from "@tauri-apps/plugin-dialog";
import { useSinglePaletteStore } from "@/hooks/store";
import { zoneNameMapping } from "@/lib/zoneNameMapping";

export default function Header({
  id,
  zone_id,

}: {
  id: string;
  zone_id: string;
  
}) {
  const selectedTubes = useTubesStore((state) => state.selectedTubes);

  const router = useNavigate();
  const fetchArchives = useArchiveStore((state) => state.fetchArchives);
  const archives = useArchiveStore((state) => state.archives);
  const { singlePaletteZoneIDs } = useSinglePaletteStore();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [rows, setRows] = useState<number>(0);
  const [columns, setColumns] = useState<number>(0);
  const [corner, setCorner] = useState<number>(0);
  const [direction, setDirection] = useState<number>(0);
  const setIsLoading = useLoadingStore((state) => state.setIsLoading);
  const isLoading = useLoadingStore((state) => state.isLoading);

  const setToastMessage = useToastStore((state) => state.setToastMessage);
  const setShowSuccessToast = useToastStore(
    (state) => state.setShowSuccessToast,
  );
  const setSortingConfig = useSortingConfigStore(
    (state) => state.setSortingConfig,
  );

  const handleDelete = async () => {
    if (selectedTubes.length === 0) {
      await message(
        "Keine Röhren ausgewählt, bitte wählen Sie zuerst einige Barcodes aus",
        {
          title: "Archives",
          kind: "warning",
          okLabel: "Got it!",
        },
      );
      return;
    }

    setShowDeleteDialog(true);
  };
  const setHighlightedTube = useTubesStore((state) => state.setHighlightedTube);
  const setSelectedTubes = useTubesStore((state) => state.setSelectedTubes);

  const setTubes = useTubesStore((state) => state.setTubes);
  const confirmDelete = async () => {
    try {
      setIsLoading(true);
      setHighlightedTube({
        content: { color: "", fluid_level: 0, line_code: "0", type: "",added_time:"" },
        position: 0,
      });

      // Get the current tubes from the store
      const currentTubes = useTubesStore.getState().tubes;

      // Create a list of tube IDs to be deleted
      const tubeIdsToDelete = selectedTubes.map(
        (tube) => tube.content.line_code,
      );

      // Update the UI immediately (optimistic update)
      const updatedTubes = currentTubes.filter(
        (tube) => !tubeIdsToDelete.includes(tube.content.line_code),
      );

      // Update the store with the filtered tubes
      setTubes(updatedTubes);
      // console.log(updatedTubes)
      // Clear selections
      setSelectedTubes([]);

      // Now perform the actual deletion on the server
      const result = await deleteArchive(tubeIdsToDelete);

      if (!result) {
        throw new Error("Zurücksetzen des Archivs fehlgeschlagen");
      }

      // Show success message
      setToastMessage(`Proben erfolgreich gelöscht`);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);

      // Refresh data from server in the background
      fetchArchives().catch((error) => {
        console.error("Archiv konnte nicht aktualisiert werden:", error);
      });
    } catch (error) {
      console.error("Proben konnten nicht gelöscht werden:", error);
      await message("Failed to delete tubes.", {
        title: "Archives",
        kind: "error",
        okLabel: "Got it!",
      });

      // Refresh to ensure UI is in sync with server state
      handleRefresh();
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      setShowDeleteDialog(false);
    }
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    setIsRefreshing(true);

    try {
      // Fetch the latest archives
      await fetchArchives();

      // Find the correct archive based on zone_id
      const selectArchive = archives.find(
        (archive) => archive.zone_id === Number(zone_id),
      );

      if (!selectArchive) {
        throw new Error("Archiv nicht gefunden");
      }

      let updatedTubes = [];

    
        if (singlePaletteZoneIDs.map(String).includes(zone_id)) {
          updatedTubes = selectArchive.zone.zone_items;
        } else {
          updatedTubes =
            selectArchive?.zone.subzones[Number.parseInt(id as string, 10) - 1]
              ?.zone.zone_items || [];
        }
      
      setTubes(updatedTubes);
      setToastMessage("Proben erfolgreich aktualisiert");
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);
    } catch (error) {
      console.error("Error refreshing tubes:", error);
      await message("Failed to refresh tubes.", {
        title: "Archives",
        kind: "error",
        okLabel: "Got it!",
      });
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  };

  const handleGoBack = async (type: "back" | "archives") => {
    if (selectedTubes.length > 0) {
      const answer = await ask(
        `Sie haben ${selectedTubes.length} Probe ausgewählt. Wenn Sie diese Seite verlassen, wird Ihre Auswahl aufgehoben.`,
        {
          title: "Sind Sie sicher?",
          kind: "warning",
          cancelLabel: "Abbrechen",
          okLabel: "Verlassen",
        },
      );
      if (answer) {
        setSelectedTubes([]);
        if (type === "archives") {
          router("/");
        } else {
          router(-1);
        }
      }
      // If user cancels, do nothing
      return;
    }
    if(type === "back"){
      if(singlePaletteZoneIDs.map(String).includes(zone_id) ) {
        return router("/");
      }
      router(-1);
    }
       if (type === "archives") {
      router("/");
    } 
  };

  return (
    <>
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-card/80 backdrop-blur-md dark:bg-gray-800/90 p-4 flex justify-between items-center sticky top-0 z-10 border-b border-border/50 shadow-sm"
      >
        <div className="flex items-center">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={()=>handleGoBack("back")}
                  className="mr-2 group"
                >
                  <ArrowLeft className="h-4 w-4 transition-transform duration-300 group-hover:-translate-x-1" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Zurück</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <Breadcrumb className="px-2">
            <BreadcrumbList>
              <BreadcrumbItem>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                  size="icon"
                  variant="ghost"
                  onClick={()=>handleGoBack("archives")}
                  className="mr-2 group"
                >
                 Archives
                </Button>
                </motion.div>
              </BreadcrumbItem>
              <BreadcrumbSeparator>
                <Slash className="h-3 w-3 text-muted-foreground/70" />
              </BreadcrumbSeparator>
              <BreadcrumbItem>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  
                    <Button
                  size="icon"
                  variant="ghost"
                  onClick={()=>handleGoBack("back")}
                  className="mx-24 group"
                >
                 
                     {zoneNameMapping[Number.parseInt(zone_id)]}
                     
                </Button>
                  
                </motion.div>
              </BreadcrumbItem>
              <BreadcrumbSeparator>
                <Slash className="h-3 w-3 text-muted-foreground/70" />
              </BreadcrumbSeparator>
              <BreadcrumbItem>
                <BreadcrumbPage className="font-medium">
                  Pallete {id}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>

        <div className="flex items-center space-x-3">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowTestDialog(true)}
                  disabled={isLoading}
                >
                  Test Dialog
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Test Dialog öffnen</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="relative overflow-hidden"
                  onClick={handleRefresh}
                  disabled={isLoading}
                >
                  <motion.div
                    animate={isRefreshing ? { rotate: 360 } : { rotate: 0 }}
                    transition={{
                      duration: 1,
                      ease: "linear",
                      repeat: isRefreshing ? Number.POSITIVE_INFINITY : 0,
                    }}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </motion.div>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Aktualisieren proben </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="relative">
                  <Button
                    variant="destructive"
                    size="icon"
                    onClick={handleDelete}
                    className="relative"
                    disabled={isLoading}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                  {selectedTubes.length > 0 && (
                    <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
                      {selectedTubes.length}
                    </span>
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Ausgewählte Rohre löschen</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </motion.header>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Löschen bestätigen
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <p>
                Diese Aktion kann nicht rückgangig gemacht werden. Sind Sie
                sicher das Sie fortahren möchten?
              </p>
              <div className="max-h-40 overflow-auto rounded border border-border p-2 text-xs">
                <p className="mb-2 font-medium">
                  Die folgenden Proben werden aus dem Archiv gelöscht (
                  {selectedTubes.length}):
                </p>
                {selectedTubes.map((tube, i) => (
                  <div
                    key={tube.content.line_code}
                    className="flex items-center gap-2 py-1 border-b border-border/50 last:border-0"
                  >
                    <span className="text-muted-foreground">{i + 1}:</span>
                    <span>{tube.content.line_code}</span>
                  </div>
                ))}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Löschen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Test Dialog */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Test Dialog</DialogTitle>
            <DialogDescription>
              Eingabe von rows, columns, corner und direction (nur ganze Zahlen)
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="rows">Rows</Label>
              <Input
                id="rows"
                type="number"
                value={rows}
                onChange={(e) =>
                  setRows(Number.parseInt(e.target.value, 10) || 0)
                }
                placeholder="Enter rows"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="columns">Columns</Label>
              <Input
                id="columns"
                type="number"
                value={columns}
                onChange={(e) =>
                  setColumns(Number.parseInt(e.target.value, 10) || 0)
                }
                placeholder="Enter columns"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="corner">Corner (1=top-left, 2=top-right, 3=bottom-right, 4=bottom-left)</Label>
              <Input
                id="corner"
                type="number"
                min="1"
                max="4"
                value={corner}
                onChange={(e) => {
                  const val = Number.parseInt(e.target.value, 10) || 0;
                  setCorner(val);
                  // Reset direction if invalid combination
                  if (val === 1 && (direction === 3 || direction === 4)) {
                    setDirection(1);
                  } else if (val === 2 && (direction === 1 || direction === 4)) {
                    setDirection(2);
                  } else if (val === 3 && (direction === 1 || direction === 2)) {
                    setDirection(3);
                  } else if (val === 4 && (direction === 2 || direction === 3)) {
                    setDirection(1);
                  }
                }}
                placeholder="Enter corner (1-4)"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="direction">
                Direction (1=right, 2=down, 3=left, 4=up)
                {corner === 1 && " - Valid: 1 (right), 2 (down)"}
                {corner === 2 && " - Valid: 2 (down), 3 (left)"}
                {corner === 3 && " - Valid: 3 (left), 4 (up)"}
                {corner === 4 && " - Valid: 1 (right), 4 (up)"}
              </Label>
              <Input
                id="direction"
                type="number"
                min="1"
                max="4"
                value={direction}
                onChange={(e) => {
                  const val = Number.parseInt(e.target.value, 10) || 0;
                  setDirection(val);
                }}
                placeholder="Enter direction (1-4)"
              />
              {(corner === 1 && (direction === 3 || direction === 4)) ||
              (corner === 2 && (direction === 1 || direction === 4)) ||
              (corner === 3 && (direction === 1 || direction === 2)) ||
              (corner === 4 && (direction === 2 || direction === 3)) ? (
                <p className="text-sm text-destructive">
                  Invalid combination! Corner {corner} cannot go {direction === 1 ? "right" : direction === 2 ? "down" : direction === 3 ? "left" : "up"}.
                </p>
              ) : null}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTestDialog(false)}>
              Cancel
            </Button>
            <Button
              disabled={
                rows <= 0 ||
                columns <= 0 ||
                corner < 1 ||
                corner > 4 ||
                direction < 1 ||
                direction > 4 ||
                !(
                  (corner === 1 && (direction === 1 || direction === 2)) ||
                  (corner === 2 && (direction === 2 || direction === 3)) ||
                  (corner === 3 && (direction === 3 || direction === 4)) ||
                  (corner === 4 && (direction === 1 || direction === 4))
                )
              }
              onClick={() => {
                // Validate inputs
                if (rows <= 0 || columns <= 0 || corner < 1 || corner > 4 || direction < 1 || direction > 4) {
                  setToastMessage("Bitte geben Sie gültige Werte ein");
                  setShowSuccessToast(true);
                  setTimeout(() => setShowSuccessToast(false), 3000);
                  return;
                }
                
                // Validate corner/direction combination
                const isValid =
                  (corner === 1 && (direction === 1 || direction === 2)) ||
                  (corner === 2 && (direction === 2 || direction === 3)) ||
                  (corner === 3 && (direction === 3 || direction === 4)) ||
                  (corner === 4 && (direction === 1 || direction === 4));
                
                if (!isValid) {
                  setToastMessage(
                    `Ungültige Kombination! Ecke ${corner} kann nicht in Richtung ${direction} gehen.`,
                  );
                  setShowSuccessToast(true);
                  setTimeout(() => setShowSuccessToast(false), 3000);
                  return;
                }
                
                setSortingConfig({ rows, columns, corner, direction });
                setShowTestDialog(false);
                setToastMessage(
                  `Sortierung angewendet: ${rows}×${columns}, Ecke ${corner}, Richtung ${direction}`,
                );
                setShowSuccessToast(true);
                setTimeout(() => setShowSuccessToast(false), 3000);
              }}
            >
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
