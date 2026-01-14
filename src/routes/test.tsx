// ArchivDataComponent.tsx
import { useArchiveStore } from "@/hooks/store";
import React from "react";
import { Link } from "react-router-dom";

// interface ArchiveItem {
//   [key: string]: any;
// }

const ArchivDataComponent: React.FC = () => {
  //  const [archives, setArchives] = useState<ZoneData[]>([]);
  const archives = useArchiveStore((state) => state.archives);
  //  const [isLoading, setIsLoading] = useState(true);
  //  const [error, setError] = useState<string | null>(null);

  // useEffect(() => {

  //   async function fetchData() {
  //     try {
  //       // getArchivesData is assumed to return an array of ZoneData objects.
  //       const archivesData = await getArchivesData();
  //       console.log("Archives Data:", archivesData);

  //       // Optionally, if you still need to parse JSON strings in fields:
  //       const formattedData = archivesData.map((item: any) => deepParseJSONFields(item));
  //       setArchives(formattedData);
  //     } catch (error) {
  //       // setError("An error occurred while fetching archives");
  //       console.error("Error fetching archives data:", error);
  //     } finally {
  //       // setIsLoading(false);
  //     }
  //   }

  //   fetchData();
  // }, []);

  return (
    <div>
      <h2>Archiv Data</h2>
      <Link to={"/"}>Go back</Link>
      <pre>{JSON.stringify(archives[0].zone.subzones[0], null, 2)}</pre>
      <ul>
        {archives.length > 0 ? (
          archives.map((item, index) => (
            <li key={index} className="dark:bg-gray-800 bg-green-300 p-4 m-4">
              <pre>{JSON.stringify(item, null, 2)}</pre>
            </li>
          ))
        ) : (
          <p>Loading...</p>
        )}
      </ul>
    </div>
  );
};

export default ArchivDataComponent;
