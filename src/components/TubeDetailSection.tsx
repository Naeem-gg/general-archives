import { motion, AnimatePresence } from "framer-motion";
import { X, Info, Droplets, Beaker, Barcode, Hash, Timer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { useTubesStore } from "@/hooks/store";
import { getRowColumn } from "@/lib/getRowColumn"
import { useMemo } from "react";


export default function Details({ isFourthRack,zoneId }: { isFourthRack?: boolean,zoneId: string }) {
  const { highlightedTube, setHighlightedTube, setSelectedTubes } =
    useTubesStore();

// read the 1-based grid index that Tubes sets on click
const index = useTubesStore((s) => s.index);

// match the same column logic as in <Tubes />
const columnsCount = zoneId === "17" ? 20 : isFourthRack ? 10 : 5;

// compute row/column directly from the current grid index
const rowCol = useMemo(() => {
  if (!index || index <= 0) {
    // fallback if index isn't set yet (e.g., programmatic highlight)
    return getRowColumn(highlightedTube.position, !!isFourthRack, zoneId);
  }
  return {
    row: Math.ceil(index / columnsCount),
    column: ((index - 1) % columnsCount) + 1,
  };
}, [index, columnsCount, highlightedTube.position, isFourthRack, zoneId]);


  const resetSelection = () => {
    setHighlightedTube({
      content: { color: "", fluid_level: 0, line_code: "0", type: "", added_time: "" },
      position: 0,
    });
    setSelectedTubes([]);
  };

  const hasTube = highlightedTube.content.line_code !== "0";

  return (
    <div className="p-2 flex flex-col sticky top-0">
      <Card className="w-[30vh] overflow-hidden border border-border/50 bg-card/30 backdrop-blur-sm">
        <CardHeader className="border-b border-border/50 bg-muted/30 p-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">Proben-Details</CardTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={resetSelection}
              className="h-8 w-8 rounded-full hover:bg-destructive/10 hover:text-destructive"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <CardDescription>
            {hasTube
              ? "Detaillierte Ansicht der ausgewählten Probe."
              : "Wählen Sie eine Probe aus, um die Details anzuzeigen."}
          </CardDescription>
        </CardHeader>

        <ScrollArea className="flex-grow">
          <CardContent className="p-4">
            <AnimatePresence mode="wait">
              {!hasTube ? (
                <motion.div
                  key="empty-state"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center py-12 text-center"
                >
                  <Info className="h-12 w-12 mb-4 text-muted-foreground opacity-20" />
                  <p className="text-lg font-medium">Keine Probe ausgewählt</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Bitte wählen Sie in der Übersicht eine Probe aus.
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="tube-details"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  {/* Identifikation */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Barcode className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-medium">Identifikationsdaten</h3>
                    </div>
                    <Separator />
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Barcode</p>
                        <p className="font-mono font-medium">
                          {highlightedTube.content.line_code}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Position</p>
                        <div className="flex items-center gap-1">
                          <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                          <p className="font-medium">{highlightedTube.position}</p>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Reihe</p>
                        <div className="flex items-center gap-1">
                          <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                          <p className="font-medium"> {rowCol.row}</p>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Spalte</p>
                        <div className="flex items-center gap-1">
                          <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                          <p className="font-medium">
                          {rowCol.column}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Zeitstempel */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Timer className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-medium">Zeitstempel</h3>
                    </div>
                    <Separator />
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Datum</p>
                        <p className="font-mono font-medium">
                          {new Date(highlightedTube.content.added_time).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Uhrzeit</p>
                        <p className="font-mono font-medium">
                          {new Date(highlightedTube.content.added_time).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Eigenschaften */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Beaker className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-medium">Proben-Eigenschaften</h3>
                    </div>
                    <Separator />
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Typ</p>
                        <Badge variant="outline" className="font-medium">
                          {highlightedTube.content.type || "Unbekannt"}
                        </Badge>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Farbe</p>
                        <div className="flex items-center gap-2">
                          <div
                            className="h-4 w-4 rounded-full border border-border/50"
                            style={{
                              backgroundColor: highlightedTube.content.color || "transparent",
                            }}
                          />
                          <span className="font-medium">
                            {highlightedTube.content.color || "Nicht verfügbar"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Flüssigkeitsstand */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Droplets className="h-5 w-5 text-primary" />
                      <h3 className="text-lg font-medium">Flüssigkeitsstand</h3>
                    </div>
                    <Separator />
                    <div className="space-y-1">
                      <div className="h-4 w-full bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all duration-500 ease-out"
                          style={{
                            width: `${Math.min(
                              100,
                              (highlightedTube.content.fluid_level || 0) * 100
                            )}%`,
                          }}
                        />
                      </div>
                      <p className="text-right text-xs text-muted-foreground">
                        {Math.round(
                          (highlightedTube.content.fluid_level || 0) * 100
                        )}
                        %
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </ScrollArea>

        <CardFooter className="border-t border-border/50 bg-muted/30 p-4">
          <Button variant="outline" size="sm" onClick={resetSelection} className="w-full">
            Auswahl zurücksetzen
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
