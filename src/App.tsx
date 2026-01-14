import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  Archive,
  ChevronRight,
  RefreshCcw
} from "lucide-react";
import { useEffect, useState } from "react";
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
import { useArchiveStore, useLanguageStore } from "./hooks/store";
import { readConfig } from "./lib/readConfig";
import { singlePaletteZoneIDsArray } from "./lib/singlePaletteZoneIDsArray";
import { zoneNameMapping } from "./lib/zoneNameMapping";

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

export default function ArchivesDashboard() {
  const fetchArchives = useArchiveStore((state) => state.fetchArchives);
  const { archives, error, isLoading } = useArchiveStore();
  const [showRefreshAnimation, setShowRefreshAnimation] = useState(false);
  const language = useLanguageStore((state) => state.language);

  const handleRefresh = () => {
    setShowRefreshAnimation(true);
    fetchArchives().finally(() => {
      setTimeout(() => setShowRefreshAnimation(false), 1000);
    });
  };

  useEffect(() => {
    fetchArchives();
    
  }, [fetchArchives]);
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
            <motion.div key={i} variants={itemVariants}>
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
        {archives.map((archive) => {
          const zoneName = archive.zone.zone_name;
          if (!zoneName) return null;
          if (
            singlePaletteZoneIDsArray.includes(archive.zone_id)
          )
            return null; // Skip these archives as they are handled separately
          return (
            <motion.div key={archive.zone_id} variants={itemVariants}>
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
        <SinglePaletteArchives zoneIDs={singlePaletteZoneIDsArray} archives={archives} />
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
    </div>
  );
}
