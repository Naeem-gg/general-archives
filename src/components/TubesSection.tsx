import { AnimatePresence, motion } from "framer-motion";
import { Check, Maximize2, Minimize2, Search, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useTubesStore } from "@/hooks/store";
import { useSearchParams } from "react-router-dom";
import type { Tube } from "./types";

export default function Tubes({
  tubes,
  isFourthRack = false,
}: {
  tubes: Tube[];
  isFourthRack?: boolean;
}) {
  // store selectors
  const {
    highlightedTube,
    setHighlightedTube,
    selectedTubes,
    setSelectedTubes,
  } = useTubesStore();
  const setIndex = useTubesStore((s) => s.setIndex);

  // state & refs
  const [searchQuery, setSearchQuery] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [startPosition, setStartPosition] = useState({ x: 0, y: 0 });
  const [scrollOffset, setScrollOffset] = useState({ left: 0, top: 0 });
  const [showScrollIndicator, setShowScrollIndicator] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [tubeDimensions, setTubeDimensions] = useState({ width: 170, height: 170 });

  const containerRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  // search-param highlighting
  const [searchParams] = useSearchParams();
  const searchedLineCode = searchParams.get("line_code");
  const zone_id = searchParams.get("zone_id");
  const lastSearchedRef = useRef<string | null>(null);

  // determine number of columns
  const columnsCount =
    zone_id === "17" ? 10 :
      isFourthRack ? 10 :
        5;

  // highlight via URL
  useEffect(() => {
    if (
      searchedLineCode &&
      searchedLineCode !== lastSearchedRef.current &&
      tubes.length
    ) {
      const tubeToHighlight = tubes.find(
        (t) => t.content.line_code === searchedLineCode
      );
      if (tubeToHighlight) {
        setHighlightedTube(tubeToHighlight);
        const el = document.getElementById(searchedLineCode);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
        lastSearchedRef.current = searchedLineCode;
      }
    }
  }, [searchedLineCode, tubes, setHighlightedTube]);

  // search filter
  const filteredTubes = useMemo(() => {
    if (!searchQuery.trim()) return tubes;
    const q = searchQuery.toLowerCase();
    return tubes.filter(
      (tube) =>
        tube.content.line_code.toString().toLowerCase().includes(q) ||
        tube.position.toString().includes(q)
    );
  }, [searchQuery, tubes]);

  // map position -> tube
  const tubeMap = useMemo(() => {
    const m = new Map<number, Tube>();
    tubes.forEach((t) => m.set(t.position, t));
    return m;
  }, [tubes]);

  // dynamic min/max from data (works up to 200+)
  const { minPosition, maxPosition } = useMemo(() => {
    if (!tubes.length) return { minPosition: 1, maxPosition: 1 };
    const positions = tubes.map((t) => t.position);
    return {
      minPosition: Math.min(...positions),
      maxPosition: Math.max(...positions),
    };
  }, [tubes]);

  const gridPositions = useMemo(() => {
    if (!tubes.length) return [];
    return Array.from({ length: maxPosition - minPosition + 1 }, (_, i) => i + minPosition);
  }, [minPosition, maxPosition, tubes]);

  // Build rows of size 20 (1..20, 21..40, …), keep only rows that
  // have at least one *real* tube, but include placeholders for the
  // missing positions inside those rows. Return rows in reverse order.
  // const zone17Positions = useMemo(() => {
  //   if (!tubes.length) return [] as number[];

  //   const chunkSize = 20;
  //   const max = maxPosition;                 // from your memo
  //   const totalChunks = Math.max(1, Math.ceil(max / chunkSize));

  //   const rows: number[][] = [];
  //   for (let c = 1; c <= totalChunks; c++) {
  //     const start = (c - 1) * chunkSize + 1;
  //     // const end = c * chunkSize;             // NOTE: not clamped to max
  //     const row = Array.from({ length: chunkSize }, (_, i) => start + i);
  //     rows.push(row);
  //   }

  //   return rows.reverse().flat();            // top chunk first (e.g., 181..200)
  // }, [maxPosition, tubes.length]);

  // Enhanced positions calculation for all zones with missing tubes
  const enhancedPositions = useMemo(() => {
    if (zone_id === "17") {
      // Zone 17: 200 positions (1-200), 20 columns, reverse chunk order
      const allPositions = Array.from({ length: 200 }, (_, i) => i + 1);
      const chunkSize = 10;
      const totalChunks = Math.ceil(allPositions.length / chunkSize);

      const rows: number[][] = [];
      for (let c = 1; c <= totalChunks; c++) {
        const start = (c - 1) * chunkSize + 1;
        const row = Array.from({ length: chunkSize }, (_, i) => start + i);
        rows.push(row);
      }

      return rows.reverse().flat(); // top chunk first (e.g., 181..200)
    } else if (isFourthRack) {
      // Fourth rack / zone 15: 50 positions (1-50), 10 columns, column-major then flip both axes
      const allPositions = Array.from({ length: 50 }, (_, i) => i + 1);
      const out: number[] = [];
      const rowsCount = Math.ceil(allPositions.length / 10);

      for (let row = 0; row < rowsCount; row++) {
        for (let col = 0; col < 10; col++) {
          const idx = col * rowsCount + row; // column-major
          if (idx < allPositions.length) out.push(allPositions[idx]);
        }
      }
      return out.reverse();
    } else {
      // Default zones (15 & 16): 50 positions (1-50), 5 columns, reverse-chunk
      const allPositions = Array.from({ length: 50 }, (_, i) => i + 1);
      const result: number[] = [];
      const chunkSize = 5;
      const numChunks = Math.ceil(allPositions.length / chunkSize);

      for (let i = numChunks - 1; i >= 0; i--) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, allPositions.length);
        for (let j = start; j < end; j++) result.push(allPositions[j]);
      }
      return result;
    }
  }, [zone_id, isFourthRack]);

  // calculate tube size
  const calculateTubeDimensions = () => {
    if (!gridRef.current || !containerRef.current) return;
    const cw = containerRef.current.clientWidth;
    const padding = 48; // 24px each side
    const gap = 16;
    const available = cw - padding - gap * (columnsCount - 1);
    const w = Math.floor(available / columnsCount);
    const size = Math.max(120, Math.min(w, 200));
    setTubeDimensions({ width: size, height: size });
  };

  useEffect(() => {
    calculateTubeDimensions();
    window.addEventListener("resize", calculateTubeDimensions);
    return () => window.removeEventListener("resize", calculateTubeDimensions);
  }, [tubes, isFourthRack, columnsCount]);

  // helper: reverse-chunk order (e.g., 181–200 on top, ... 1–20 bottom)
  // const rearrangeArray = (arr: number[]) => {
  //   const result: number[] = [];
  //   const chunkSize = columnsCount;
  //   const numChunks = Math.ceil(arr.length / chunkSize);
  //   for (let i = numChunks - 1; i >= 0; i--) {
  //     const start = i * chunkSize;
  //     const end = Math.min(start + chunkSize, arr.length);
  //     for (let j = start; j < end; j++) result.push(arr[j]);
  //   }
  //   return result;
  // };

  // rows count
  // const rowsCount = useMemo(
  //   () => Math.ceil(gridPositions.length / columnsCount),
  //   [gridPositions.length, columnsCount]
  // );

  // display order per spec
  //   const displayPositions = useMemo<number[]>(() => {
  //     if (!gridPositions.length) return [];

  //     // Fourth rack / zone 15: column-major then flip both axes
  //     if (isFourthRack) {
  //   // keep your special fourth-rack layout here (unchanged)
  //   const out: number[] = [];
  //   for (let row = 0; row < rowsCount; row++) {
  //     for (let col = 0; col < columnsCount; col++) {
  //       const idx = col * rowsCount + row; // column-major
  //       if (idx < gridPositions.length) out.push(gridPositions[idx]);
  //     }
  //   }
  //   return out.reverse();
  // }

  // if (zone_id == "17") {
  //   // 20 columns, reverse-chunk (top has highest range)
  //   return zone17Positions;
  // }

  // // default (incl. zone 15 & 16): 5 columns, reverse-chunk -> 46..50, 41..45, … 1..5
  // return rearrangeArray(gridPositions);
  //   }, [gridPositions, columnsCount, rowsCount, isFourthRack, zone_id]);

  // selection handlers
  const toggleTubeSelection = (tube: Tube) => {
    setHighlightedTube(tube);
    const exists = selectedTubes.some(
      (t) => t.content.line_code === tube.content.line_code
    );
    setSelectedTubes(
      exists
        ? selectedTubes.filter((t) => t.content.line_code !== tube.content.line_code)
        : [...selectedTubes, tube]
    );
  };

  const selectAllTubes = () => {
    setSelectedTubes(selectedTubes.length === filteredTubes.length ? [] : filteredTubes);
  };

  // drag-to-scroll
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!scrollRef.current) return;
    setIsDragging(true);
    setStartPosition({ x: e.clientX, y: e.clientY });
    setScrollOffset({
      left: scrollRef.current.scrollLeft,
      top: scrollRef.current.scrollTop,
    });
    setShowScrollIndicator(true);
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !scrollRef.current) return;
    e.preventDefault();
    const dx = startPosition.x - e.clientX;
    const dy = startPosition.y - e.clientY;
    scrollRef.current.scrollLeft = scrollOffset.left + dx;
    scrollRef.current.scrollTop = scrollOffset.top + dy;
  };
  const handleMouseUp = () => {
    setIsDragging(false);
    setTimeout(() => setShowScrollIndicator(false), 500);
  };

  // controls
  const clearSearch = () => setSearchQuery("");
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    setTimeout(calculateTubeDimensions, 0);
  };

  const isSearching = !!searchQuery.trim();
  const commonStyle = {
    width: `${tubeDimensions.width}px`,
    height: `${tubeDimensions.height}px`,
  };

  // empty-state
  if (!gridPositions.length) {
    return (
      <div
        ref={containerRef}
        className={`flex-grow h-[89vh] flex flex-col overflow-hidden bg-card/30 backdrop-blur-sm rounded-lg border border-border/50 transition-all duration-300 ${isFullscreen ? "fixed inset-4 z-50" : ""
          }`}
      >
        <div
          ref={scrollRef}
          className="flex-grow relative overflow-auto cursor-grab active:cursor-grabbing"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${columnsCount}, minmax(${tubeDimensions.width}px, 1fr))`,
              gap: "16px",
              minWidth: isFullscreen ? "auto" : "54rem",
            }}
          >
            {enhancedPositions.map((pos) => (
              <motion.div
                key={`missing-${pos}`}
                layout
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 0.5, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.2 }}
                className="rounded-lg overflow-hidden flex flex-col items-center justify-center shadow-inner bg-gray-200 dark:bg-gray-700 border border-dashed border-border/50"
                style={commonStyle}
              >
                <span className="text-xs text-muted-foreground">Leer #{pos}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // main render
  return (
    <div
      ref={containerRef}
      className={`flex-grow h-[89vh] flex flex-col overflow-hidden bg-card/30 backdrop-blur-sm rounded-lg border border-border/50 transition-all duration-300 ${isFullscreen ? "fixed inset-4 z-50" : ""
        }`}
    >
      {/* header */}
      <div className="p-4 border-b border-border/50 flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search tubes..."
            className="pl-9 pr-9 h-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {isSearching && (
            <button onClick={clearSearch} className="absolute right-2.5 top-2.5">
              <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
            </button>
          )}
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          <Badge variant="outline" className="h-7 px-3">
            {filteredTubes.length} Proben
          </Badge>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={selectAllTubes} className="h-7 px-3">
                  <Check className="mr-1 h-3.5 w-3.5" />
                  {selectedTubes.length === filteredTubes.length ? "Alle abwählen" : "Alle auswählen"}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>
                  {selectedTubes.length === filteredTubes.length
                    ? "Alle abwählen proben"
                    : "Alle auswählen proben"}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={toggleFullscreen} className="h-7 w-7">
                  {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* grid */}
      <div
        ref={scrollRef}
        className="flex-grow relative overflow-auto cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <AnimatePresence>
          {showScrollIndicator && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center"
            >
              <div className="bg-black/20 dark:bg-white/20 backdrop-blur-sm rounded-full p-3">
                <Search className="h-6 w-6 text-white dark:text-black" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div
          ref={gridRef}
          className="p-6"
          style={{
            display: "grid",
            gridTemplateColumns: `repeat(${columnsCount}, minmax(${tubeDimensions.width}px, 1fr))`,
            gap: "16px",
            minWidth: isFullscreen ? "auto" : "54rem",
          }}
        >
          <AnimatePresence>
            {isSearching
              ? filteredTubes.map((tube, idx) => (
                <motion.div
                  key={tube.content.line_code}
                  layout
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ duration: 0.2 }}
                  id={tube.content.line_code.toString()}
                  onClick={() => {
                    setHighlightedTube(tube);
                    setIndex(idx + 1);
                  }}
                  className={`cursor-pointer rounded-lg overflow-hidden flex flex-col shadow-md transition-shadow duration-300 hover:shadow-lg ${highlightedTube?.content.line_code === tube.content.line_code
                      ? "ring-4 ring-primary ring-offset-4 ring-offset-background"
                      : "group bg-card/30 border border-border/50 backdrop-blur-sm"
                    }`}
                  style={commonStyle}
                >
                  <div
                    className={`h-1/2 flex items-center justify-center p-6 border-b ${tube.content.line_code
                        ? "bg-gradient-to-r from-muted/80 to-muted/30 group-hover:from-primary/10 group-hover:to-primary/5"
                        : "bg-gray-400"
                      }`}
                  >
                    <span>{tube.content.line_code || "No Barcode"}</span>
                  </div>
                  <div className="h-1/2 p-3 flex flex-col justify-between bg-card dark:bg-gray-800">
                    <label className="flex items-center space-x-2 text-sm">
                      <Checkbox
                        checked={selectedTubes.some(
                          (t) => t.content.line_code === tube.content.line_code
                        )}
                        onCheckedChange={() => toggleTubeSelection(tube)}
                        className="data-[state=checked]:bg-primary"
                      />
                      <div className="w-full flex justify-between">
                        <span>Select</span>
                        <span
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: tube.content.color }}
                          title={tube.content.color}
                        />
                      </div>
                    </label>
                    <div className="text-xs text-right text-muted-foreground">#{tube.position}</div>
                  </div>
                </motion.div>
              ))
              : enhancedPositions.map((pos) => {
                const tube = tubeMap.get(pos);
                return tube ? (
                  <motion.div
                    key={tube.content.line_code}
                    layout
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.2 }}
                    id={tube.content.line_code.toString()}
                    onClick={() => {
                      setHighlightedTube(tube);
                      setIndex(enhancedPositions.indexOf(pos) + 1);
                    }}
                    className={`rounded-lg overflow-hidden flex flex-col shadow-md transition-shadow duration-300 hover:shadow-lg ${highlightedTube?.content.line_code === tube.content.line_code
                        ? "ring-4 ring-primary ring-offset-4 ring-offset-background"
                        : "group bg-card/30 border border-border/50 backdrop-blur-sm"
                      }`}
                    style={commonStyle}
                  >
                    <div
                      className={`h-1/2 flex items-center justify-center p-6 border-b ${tube.content.line_code
                          ? "bg-gradient-to-r from-muted/80 to-muted/30 group-hover:from-primary/10 group-hover:to-primary/5"
                          : "bg-gray-400"
                        }`}
                    >
                      <span>{tube.content.line_code}</span>
                    </div>
                    <div className="h-1/2 p-3 flex flex-col justify-between bg-card dark:bg-gray-800">
                      <label className="flex items-center space-x-2 text-sm">
                        <Checkbox
                          checked={selectedTubes.some(
                            (t) => t.content.line_code === tube.content.line_code
                          )}
                          onCheckedChange={() => toggleTubeSelection(tube)}
                          className="data-[state=checked]:bg-primary"
                        />
                        <div className="w-full flex justify-between">
                          <span>Select</span>
                          <span
                            className="w-4 h-4 rounded-full"
                            style={{ backgroundColor: tube.content.color }}
                            title={tube.content.color}
                          />
                        </div>
                      </label>
                      <div className="text-xs text-right text-muted-foreground">#{tube.position}</div>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key={`missing-${pos}`}
                    layout
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 0.5, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.2 }}
                    className="rounded-lg overflow-hidden flex flex-col items-center justify-center shadow-inner bg-gray-200 dark:bg-gray-700 border border-dashed border-border/50"
                    style={commonStyle}
                  >
                    <span className="text-xs text-muted-foreground">Leer #{pos}</span>
                  </motion.div>
                );
              })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
