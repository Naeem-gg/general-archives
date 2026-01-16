import { useEffect, useState } from "react";
import { useArchiveStore, useLoadingStore, useTubesStore, useSinglePaletteStore } from "./store";
import { useParams, useSearchParams } from "react-router-dom";

export const useSetTubes = () => {
  const { setIsLoading } = useLoadingStore();
  const [, setError] = useState<string | null>(null);
  const fetchArchives = useArchiveStore((state) => state.fetchArchives);
  const archives = useArchiveStore((state) => state.archives);
  const { singlePaletteZoneIDs } = useSinglePaletteStore();
  const [searchParams] = useSearchParams();
  const zone_id = searchParams.get("zone_id");
  const { id } = useParams<{ id: string }>();
  const setTubes = useTubesStore((state) => state.setTubes);
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        await fetchArchives();

        // Instead of reading archives from dependencies,
        // you might want to get them from a stable source.
        const selectArchive = archives.find(
          (archive) => archive.zone_id === Number(zone_id),
        );

        if (!selectArchive) {
          setError("Archive not found");
          return;
        }
        
          //For Exchange Archives
          if (singlePaletteZoneIDs.includes(Number(zone_id))) {
            setTubes(selectArchive.zone.zone_items);
            return; // Return early to avoid further processing
          }
          //For Other Archives
          const rackTubes =
            selectArchive?.zone.subzones[Number.parseInt(id as string, 10) - 1]
              ?.zone.zone_items;
          if (!rackTubes) {
            setError("Rack data not found");
          } else {
            setTubes(rackTubes);
          }
        
      } catch (err) {
        setError("Failed to load rack data");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    if (zone_id && id) {
      loadData();
    } else {
      setError("Missing required parameters");
      setIsLoading(false);
    }
  }, [zone_id, id]); // Removed archives and fetchArchives from dependencies
};
