import { writeTextFile, BaseDirectory } from "@tauri-apps/plugin-fs";

export const writeConfig = async (config: { HOST: string; PORT: string }) => {
  try {
    const contents = JSON.stringify(config);
    await writeTextFile("Diabots\\config.json", contents, {
      baseDir: BaseDirectory.AppLocalData,
    });
  } catch (error) {
    throw new Error("Failed to write config, error: " + error);
  }
};
