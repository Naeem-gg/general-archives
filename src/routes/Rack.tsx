import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import Header from "@/components/Header";
import Details from "@/components/TubeDetailSection";
import Tubes from "@/components/TubesSection";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useLoadingStore, useToastStore, useTubesStore } from "@/hooks/store";
import { useSetTubes } from "@/hooks/useSetTubes";
import { AlertCircle, Check } from "lucide-react";

export default function Rack() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const zone_id = searchParams.get("zone_id");

  const { isLoading } = useLoadingStore();
  // const setIsLoading = useLoadingStore((state) => state.setIsLoading)
  const [error] = useState<string | null>(null);

  const tubes = useTubesStore((state) => state.tubes);

  const setHighlightedTube = useTubesStore((state) => state.setHighlightedTube);

  const showSuccessToast = useToastStore((state) => state.showSuccessToast);
  const toastMessage = useToastStore((state) => state.toastMessage);
  useEffect(() => {
    setHighlightedTube({
      content: { color: "", fluid_level: 0, line_code: "0", type: "",added_time:"" },
      position: 0,
    });
  }, []);
  useSetTubes();
  // if(id=="4")return <div><Header id={id} zone_id={zone_id as string} archiveNumber={archiveNumber} /><h1>its 4th rack</h1></div>
  if (!zone_id || !id) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-background to-background/80 p-6">
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
            <AlertCircle className="h-5 w-5" color="white" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {!zone_id ? "Zone ID not found" : "Rack ID not found"}
            </AlertDescription>
          </Alert>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-background to-background/80 dark:from-gray-900 dark:to-gray-950 dark:text-white select-none">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.02] pointer-events-none"></div>

      <Header id={id} zone_id={zone_id}/>

      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-grow flex flex-col md:flex-row p-6 gap-6"
          >
            <div className="flex-grow overflow-hidden bg-card/30 backdrop-blur-sm rounded-lg border border-border/50">
              <div className="p-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
                {[...Array(15)].map((_, i) => (
                  <Skeleton key={i} className="w-full h-40 rounded-lg" />
                ))}
              </div>
            </div>
            <Skeleton className="w-full md:w-1/3 h-[calc(100vh-180px)] rounded-lg" />
          </motion.div>
        ) : error ? (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-grow flex items-center justify-center p-6"
          >
            <Alert
              variant="destructive"
              className="backdrop-blur-sm bg-destructive/90 border border-destructive/20 shadow-lg max-w-md text-white"
            >
              <AlertCircle className="h-5 w-5" color="white" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </motion.div>
        ) : (
          <motion.main
            key="content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-grow flex flex-col md:flex-row overflow-hidden"
          >
            <Tubes tubes={tubes} isFourthRack={id=="4"?true:false} />
            <Details  isFourthRack={id=="4"?true:false} zoneId={zone_id}/>
          </motion.main>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {showSuccessToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-4 right-4 z-50"
          >
            <div className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-3 text-white shadow-lg">
              <Check className="h-5 w-5" />
              <span>{toastMessage}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
