import {
  BaseDirectory,
  exists,
  mkdir,
  readTextFile,
  writeTextFile,
} from "@tauri-apps/plugin-fs";

export async function readConfig(): Promise<any> {
  const contents = JSON.stringify({
    HOST: "http://localhost",
    PORT: "9999",
    devOptions: "false",
  });
  try {
    const isFolderExists = await exists("Diabots", {
      baseDir: BaseDirectory.AppLocalData,
    });
    // console.log("Diabots folder check: ",isFolderExists)
    if (!isFolderExists) {
      // console.log("Inside creation of folder")
      await mkdir("Diabots", {
        baseDir: BaseDirectory.AppLocalData,
      });
    }
    const isConfigFile = await exists("Diabots\\config.json", {
      baseDir: BaseDirectory.AppLocalData,
    });
    // console.log("Config file check",isConfigFile);

    if (!isConfigFile) {
      //  console.log("Inside creation of config file")

      await writeTextFile("Diabots\\config.json", contents, {
        baseDir: BaseDirectory.AppLocalData,
      });
    }
    const configString = await readTextFile("Diabots\\config.json", {
      baseDir: BaseDirectory.AppLocalData,
    });
    const config = JSON.parse(configString);
    return config;
  } catch (error) {
    console.error("Error reading config:", error);
  }
}
