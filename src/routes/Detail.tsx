import { motion } from "framer-motion";
import { AlertCircle, ArrowLeft, Database, Server } from "lucide-react";
import { useEffect } from "react";
import {
  Link,
  useNavigate,
  useParams
} from "react-router-dom";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

import { useArchiveStore } from "@/hooks/store";
import { calculateRacks } from "@/lib/calculateRacks";
import { zoneNameMapping } from "@/lib/zoneNameMapping";
import { useSinglePaletteStore } from "@/hooks/store";

export default function Details() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { archives, isLoading, error } = useArchiveStore();
  const { singlePaletteZoneIDs, fetchSinglePallets } = useSinglePaletteStore();
  
  useEffect(() => {
    fetchSinglePallets();
  }, [fetchSinglePallets]);
  
  useEffect(() => {
    if (id && singlePaletteZoneIDs.map(String).includes(id)) {
      navigate(`/rack/1?zone_id=${id}`);
    }
  }, [id, singlePaletteZoneIDs, navigate]);

  if (!id) return null;

  if (isLoading) {
    return (
      <div className="relative min-h-screen bg-gradient-to-br from-background to-background/80">
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.02] pointer-events-none"></div>
        <div className="container mx-auto flex min-h-screen flex-col p-6 lg:p-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8 flex items-center justify-between"
          >
            <div className="space-y-1">
              <div className="flex items-center">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => navigate(-1)}
                  className="mr-4"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <Skeleton className="h-8 w-48" />
              </div>
              <Skeleton className="h-4 w-32" />
            </div>
          </motion.div>

          <Separator className="mb-8" />

          <motion.div
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: {
                  staggerChildren: 0.1,
                },
              },
            }}
            initial="hidden"
            animate="visible"
            className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
          >
            {[1, 2, 3].map((i) => (
              <motion.div
                key={i}
                variants={{
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
                }}
              >
                <Card className="h-40 overflow-hidden border border-border/50 bg-card/30 backdrop-blur-sm">
                  <CardContent className="flex h-full flex-col items-center justify-center space-y-4 p-6">
                    <Skeleton className="h-8 w-8 rounded-full" />
                    <Skeleton className="h-6 w-24" />
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative min-h-screen bg-gradient-to-br from-background to-background/80">
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.02] pointer-events-none"></div>
        <div className="container mx-auto flex min-h-screen flex-col items-center justify-center p-6 lg:p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-md"
          >
            <Alert
              variant="destructive"
              className="backdrop-blur-sm bg-destructive/90 border border-destructive/20 shadow-lg text-white"
            >
              <AlertCircle className="h-5 w-5 " color="white" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <div className="mt-6 text-center">
              <Button
                onClick={() => navigate(-1)}
                className="inline-flex items-center"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Archives
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  const archive = archives.find(
    (singleArchive) => singleArchive.zone_id == Number.parseInt(id),
  );

  if (!archive) {
    return (
      <div className="relative min-h-screen bg-gradient-to-br from-background to-background/80">
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.02] pointer-events-none"></div>
        <div className="container mx-auto flex min-h-screen flex-col items-center justify-center p-6 lg:p-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="mb-6 flex justify-center">
              <div className="rounded-full bg-muted/50 p-6">
                <Database className="h-12 w-12 text-muted-foreground" />
              </div>
            </div>
            <h1 className="mb-2 text-2xl font-semibold">Archive not found</h1>
            <p className="mb-6 text-muted-foreground">
              The archive you're looking for doesn't exist or has been removed.
            </p>
            <Button
              onClick={() => navigate("/")}
              className="inline-flex items-center"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Archives
            </Button>
          </motion.div>
        </div>
      </div>
    );
  }


  return (
    <div className="relative min-h-screen bg-gradient-to-br from-background to-background/80">
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.02] pointer-events-none"></div>
      <div className="container mx-auto flex min-h-screen flex-col p-6 lg:p-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => navigate(-1)}
                  className="mr-4 group"
                >
                  <ArrowLeft className="h-4 w-4 transition-transform duration-300 group-hover:-translate-x-1" />
                  <span className="sr-only">Back</span>
                </Button>
                <h1 className="text-2xl font-semibold tracking-tight">
                  <span className="bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                    {zoneNameMapping[archive.zone_id]}
                  </span>
                </h1>
              </div>
              <p className="text-sm text-muted-foreground">
                Ihre Übersicht über alle Archivpositionen und archivierte Proben
              </p>
            </div>

            <Badge variant="outline" className="bg-primary/5 text-primary">
              {archive.zone.subzones.length} Palette
            </Badge>
          </div>
        </motion.div>

        <Separator className="mb-8" />

        <ScrollArea className="h-[calc(100vh-180px)]">
          <motion.div
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: {
                  staggerChildren: 0.1,
                },
              },
            }}
            initial="hidden"
            animate="visible"
            className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
          >
            {archive.zone.subzones.length === 0 && (
              <div className="h-[calc(100vh-180px)] flex justify-center items-center">
                <h1 className="text-2xl font-semibold tracking-tight text-muted-foreground">
                  No racks found
                </h1>
              </div>
            )}
            {calculateRacks(archive.zone.subzones.length).map((rackNumber) => (
              <motion.div
                key={rackNumber}
                variants={{
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
                }}
                whileHover={{ y: -8, transition: { duration: 0.3 } }}
              >
                <Link
                  to={`/rack/${rackNumber}?zone_id=${archive.zone_id}`}
                  className="block h-full"
                >
                  <Card className="group h-full overflow-hidden border border-border/50 bg-card/30 backdrop-blur-sm transition-all duration-300 hover:bg-card/80 hover:shadow-lg hover:shadow-primary/5 dark:hover:shadow-primary/10">
                    <CardContent className="flex h-full flex-col items-center justify-center space-y-6 p-6">
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 transition-all duration-300 group-hover:scale-110 group-hover:bg-primary/20">
                        <Server className="h-8 w-8 text-primary transition-all duration-300" />
                      </div>
                      <div className="space-y-2 text-center">
                        <h2 className="text-xl font-medium transition-colors duration-300 group-hover:text-primary">
                          {
                            archive.zone_id == 111
                              ? rackNumber === "1"
                                ? `Pilot ${rackNumber}`
                                : rackNumber === "2"
                                  ? `Pilot ${rackNumber}`
                                  : rackNumber === "3"
                                    ? `Pilot ${rackNumber}`
                                  : `Proben ${rackNumber}`
                              : `Palette ${rackNumber}`
                          }
                        </h2>
                        <p className="text-sm text-muted-foreground">
                          {archive.zone.subzones[
                            Number.parseInt(rackNumber) - 1
                          ]?.zone.zone_items.length || 0}{" "}
                          proben
                        </p>
                      </div>
                      <div className="absolute bottom-4 right-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                        <Badge
                          variant="secondary"
                          className="bg-primary/10 text-primary"
                        >
                          Details anzeigen
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </ScrollArea>
      </div>
    </div>
  );
}
