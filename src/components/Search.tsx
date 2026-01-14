import { useNavigate } from "react-router-dom";
import { SearchIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useArchiveStore } from "@/hooks/store";
import { useCallback, useEffect, useRef, useState } from "react";
import { zoneNameMapping } from "@/lib/zoneNameMapping";

interface SearchResult {
  barcode: string;
  rackNumber: string;
  archiveName: string;
  zoneId: number;
  parentZoneId: number;
}

export function Search() {
  const router = useNavigate();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const archives = useArchiveStore((state) => state.archives);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const searchArchives = useCallback(() => {
    setIsLoading(true);
    const allResults: SearchResult[] = [];
    const queryLower = query.trim().toLowerCase();

    if (queryLower.length === 0) {
      archives.forEach((archive) => {
        if (!archive || !archive.zone || !archive.zone_id) return;
        const parentZoneId = archive.zone_id;

        if (archive.zone.zone_items) {
          archive.zone.zone_items.forEach((item: any, idx: number) => {
            if (item?.content?.line_code) {
              allResults.push({
                barcode: String(item.content.line_code),
                rackNumber: `Position ${item.position || idx + 1}`,
                archiveName: `${zoneNameMapping[parentZoneId]}`,
                zoneId: parentZoneId,
                parentZoneId: parentZoneId,
              });
            }
          });
        }

        if (archive.zone.subzones && Array.isArray(archive.zone.subzones)) {
          archive.zone.subzones.forEach((subzone: any) => {
            if (subzone?.zone?.zone_items) {
              subzone.zone.zone_items.forEach((item: any, idx: number) => {
                if (item?.content?.line_code) {
                  allResults.push({
                    barcode: String(item.content.line_code),
                    rackNumber: `Position ${item.position || idx + 1}`,
                    archiveName: `${zoneNameMapping[parentZoneId]} > Rack ${subzone.zone_id}`,
                    zoneId: subzone.zone_id,
                    parentZoneId: parentZoneId,
                  });
                }
              });
            }
          });
        }
      });
      setResults(allResults);
      setIsLoading(false);
      return;
    }

    archives.forEach((archive) => {
      const searchRecursively = (
        item: any,
        path: string[] = [],
        parentZoneId?: number,
      ) => {
        if (!item) return;
        const currentZoneId = item.zone_id || parentZoneId || 0;

        if (item.zone?.zone_items && Array.isArray(item.zone.zone_items)) {
          item.zone.zone_items.forEach((zoneItem: any, index: number) => {
            const lineCode = String(
              zoneItem?.content?.line_code || "",
            ).toLowerCase();
            if (lineCode && lineCode.includes(queryLower)) {
              allResults.push({
                barcode: String(zoneItem?.content?.line_code),
                rackNumber: `Position ${zoneItem.position || index + 1}`,
                archiveName:
                  path.length > 0
                    ? path.join(" > ")
                    : `${zoneNameMapping[currentZoneId]}`,
                zoneId: currentZoneId,
                parentZoneId: parentZoneId || currentZoneId,
              });
            }
          });
        }

        if (item.zone?.subzones && Array.isArray(item.zone.subzones)) {
          item.zone.subzones.forEach((subzone: any) => {
            const newPath = [...path];
            if (currentZoneId) newPath.push(`Rack ${subzone.zone_id}`);
            searchRecursively(subzone, newPath, currentZoneId);
          });
        }
      };

      const initialPath = archive.zone_id
        ? [`${zoneNameMapping[archive.zone_id]}`]
        : [];
      searchRecursively(archive, initialPath);
    });

    setResults(allResults);
    setIsLoading(false);
  }, [query, archives]);

  useEffect(() => {
    if (open) {
      searchArchives();
    }
  }, [open, searchArchives]);

  const handleSelect = (result: SearchResult) => {
    setOpen(false);
   
      router(
        `/rack/${result.zoneId}?zone_id=${result.parentZoneId}&line_code=${result.barcode}`,
      );
    
  };

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    const regex = new RegExp(`(${query})`, "gi");
    return text.split(regex).map((part, index) =>
      regex.test(part) ? (
        <span key={index} className="bg-primary/20 text-primary">
          {part}
        </span>
      ) : (
        part
      ),
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Button
        variant="outline"
        className={cn(
          "relative h-9 w-9 p-0 xl:h-10 xl:w-60 xl:justify-start xl:px-3 xl:py-2",
        )}
        onClick={() => setOpen(true)}
      >
        <SearchIcon className="h-4 w-4 xl:mr-2" aria-hidden="true" />
        <span className="hidden xl:inline-flex">Archiv durchsuchen ...</span>
        <span className="sr-only">Archiv durchsuchen </span>
        <kbd className="pointer-events-none absolute right-1.5 top-2 hidden h-6 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 xl:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Archiv durchsuchen </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="relative">
            <SearchIcon className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              ref={inputRef}
              placeholder="Search by barcode..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-8"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
            />
          </div>
          <ScrollArea className="h-[50vh] rounded-md border p-4">
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div
                    key={i}
                    className="h-12 w-full animate-pulse rounded-sm bg-muted"
                  />
                ))}
              </div>
            ) : results.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-center text-sm text-muted-foreground">
                  {query
                    ? `No results found for "${query}"`
                    : "Type to search..."}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-sm text-muted-foreground">
                  {results.length} result{results.length === 1 ? "" : "s"}
                </div>
                {results.map((result, index) => (
                  <button
                    key={`${result.barcode}-${index}`}
                    onClick={() => handleSelect(result)}
                    className="flex w-full items-center space-x-4 rounded-md border p-4 text-left transition-colors hover:bg-muted"
                  >
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {highlightMatch(result.barcode, query)}
                      </p>
                      <div className="flex items-center text-sm text-muted-foreground">
                        <span className="ml-2">{result.archiveName}</span>
                        <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          {result.rackNumber}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}
