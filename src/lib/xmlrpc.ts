import axios from "axios";
import { XMLParser } from "fast-xml-parser";
import { readConfig } from "./readConfig";
async function getXML_URL() {
  const config = await readConfig();
  const host = config.HOST ?? "http://localhost";
  const port = config.PORT ?? "9999";
  const XMLRPC_URL = `${host}:${port}/`;

  // You can use XMLRPC_URL here or return it if needed
  return XMLRPC_URL;
}

/**
 * Recursively convert an XML-RPC value (as produced by fast-xml-parser)
 * into plain JavaScript types.
 */
function xmlRpcValueToJson(value: any): any {
  // If value is not an object, or is null, return it directly.
  if (typeof value !== "object" || value === null) {
    return value;
  }

  // Handle basic types
  if ("i4" in value || "int" in value) {
    return Number(value.i4 || value.int);
  }
  if ("string" in value) {
    return value.string;
  }
  if ("boolean" in value) {
    // XML-RPC booleans are "0" or "1" (as strings or numbers)
    return value.boolean === "1" || value.boolean === 1;
  }
  if ("double" in value) {
    return Number(value.double);
  }

  // Handle struct
  if ("struct" in value) {
    const members = value.struct.member;
    const memberArray = Array.isArray(members) ? members : [members];
    const obj: any = {};
    memberArray.forEach((member: any) => {
      const key = member.name;
      const val = xmlRpcValueToJson(member.value);
      
      // Handle STR_ prefix for line_code values (clean solution for XML-RPC number conversion)
      if (key === "line_code") {
        if (typeof val === "string" && val.startsWith("STR_")) {
          // Remove the STR_ prefix that was added to prevent XML-RPC number conversion
          const cleanLineCode = val.substring(4); // Remove "STR_"
          // console.log(`DEBUG - Cleaned STR_ prefix: ${val} -> ${cleanLineCode}`);
          obj[key] = cleanLineCode;
        } else {
          // console.log(`DEBUG - line_code unchanged: ${val} (type: ${typeof val})`);
          obj[key] = val;
        }
      } else {
        obj[key] = val;
      }
    });
    return obj;
  }

  // Handle array
  if ("array" in value) {
    const data = value.array.data;
    // If data is empty (e.g. an empty array), return []
    if (!data || data === "") return [];
    const arr = data.value;
    if (Array.isArray(arr)) {
      return arr.map(xmlRpcValueToJson);
    } else {
      return [xmlRpcValueToJson(arr)];
    }
  }

  // Fallback: process each property
  const result: any = {};
  for (const key in value) {
    const val = xmlRpcValueToJson(value[key]);
    
    // Handle STR_ prefix for line_code values in fallback parsing
    if (key === "line_code") {
      if (typeof val === "string" && val.startsWith("STR_")) {
        // Remove the STR_ prefix that was added to prevent XML-RPC number conversion
        const cleanLineCode = val.substring(4); // Remove "STR_"
        // console.log(`DEBUG - Cleaned STR_ prefix in fallback: ${val} -> ${cleanLineCode}`);
        result[key] = cleanLineCode;
      } else {
        // console.log(`DEBUG - line_code unchanged in fallback: ${val} (type: ${typeof val})`);
        result[key] = val;
      }
    } else {
      result[key] = val;
    }
  }
  return result;
}

/**
 * Generic function to call an XML-RPC method.
 * @param methodName - The XML-RPC method to call.
 * @param params - An array of parameters to send.
 * @returns The parsed XML response.
 */
export const callXMLRPCMethod = async (
  methodName: string,
  params: any[] = [],
): Promise<any> => {
  // Build XML for parameters
  const paramsXML =
    params.length > 0
      ? `<params>
          ${params
            .map(
              (param) =>
                `<param><value>${serializeValue(param)}</value></param>`,
            )
            .join("")}
        </params>`
      : "<params></params>";

  // Construct the full XML request
  const xmlRequest = `<?xml version="1.0"?>
    <methodCall>
      <methodName>${methodName}</methodName>
      ${paramsXML}
    </methodCall>`;

  try {
    const response = await axios.post(await getXML_URL(), xmlRequest, {
      headers: { "Content-Type": "text/xml" },
    });
    if (response.data) {
      const parser = new XMLParser({
        ignoreAttributes: false,
        attributeNamePrefix: "@_",
      });
      const result = parser.parse(response.data);
      return result;
    } else {
      throw new Error("No response data");
    }
  } catch (error) {
    console.error("Error calling XML-RPC method:", error);
    throw error;
  }
};

/**
 * Helper to serialize a JavaScript value into an XML-RPC value.
 */
const serializeValue = (value: any): string => {
  if (typeof value === "string") {
    return `<string>${value}</string>`;
  } else if (typeof value === "number") {
    return `<string>${value}</string>`;
  } else if (typeof value === "boolean") {
    return `<boolean>${value ? "1" : "0"}</boolean>`;
  } else if (Array.isArray(value)) {
    return `<array><data>${value
      .map((item) => `<value>${serializeValue(item)}</value>`)
      .join("")}</data></array>`;
  } else if (typeof value === "object" && value !== null) {
    const members = Object.entries(value)
      .map(
        ([key, val]) =>
          `<member><name>${key}</name><value>${serializeValue(val)}</value></member>`,
      )
      .join("");
    return `<struct>${members}</struct>`;
  } else {
    // Fallback to string representation.
    return `<string>${value}</string>`;
  }
};

/**
 * Calls the get_archiv_data method to retrieve archive data.
 * Unwraps the XML-RPC response into a plain array.
 */
export const getArchivesData = async (): Promise<any[]> => {
  // await callXMLRPCMethod("restart",["False"])
  const result = await callXMLRPCMethod("get_archiv_data");
  // Defer heavy parsing to avoid blocking the main thread.
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        const rawValue = result?.methodResponse?.params?.param?.value;
        const parsed = xmlRpcValueToJson(rawValue);
        resolve(Array.isArray(parsed) ? parsed : [parsed]);
      } catch (error) {
        reject(error);
      }
    }, 0);
  });
};

/**
 * Calls the delete_vial_by_barcode method.
 * @param tube_id - Array of tube barcodes.
 */
export const deleteArchive = async (tube_id: string[]): Promise<boolean> => {
  const response = await callXMLRPCMethod("delete_vial_by_barcode", [
    { barcodes: tube_id },
  ]);
  // Extract the raw XML-RPC value
  const rawValue = response?.methodResponse?.params?.param?.value;
  // Convert the XML value to a JSON (boolean) value
  const parsedValue = xmlRpcValueToJson(rawValue);
  return parsedValue;
};

/**
 * Utility function to recursively parse JSON strings.
 * (Retained from your previous implementation.)
 */
export const deepParseJSONFields = (value: any): any => {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (
      (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
      (trimmed.startsWith("[") && trimmed.endsWith("]"))
    ) {
      try {
        return deepParseJSONFields(JSON.parse(value));
      } catch (e) {
        return value;
      }
    }
    return value;
  } else if (Array.isArray(value)) {
    return value.map(deepParseJSONFields);
  } else if (typeof value === "object" && value !== null) {
    const newObj: Record<string, any> = {};
    for (const key in value) {
      if (value.hasOwnProperty(key)) {
        newObj[key] = deepParseJSONFields(value[key]);
      }
    }
    return newObj;
  }
  return value;
};

/**
 * Calls the restart method on the server with a boolean argument.
 * @param value - Boolean value to pass to the restart method.
 */
export const restart = async (value: boolean): Promise<any> => {
  return await callXMLRPCMethod("restart", [value]);
};

export const resetArchives = async (): Promise<boolean> => {
  const response = await callXMLRPCMethod("reset_archives");
  // Extract the raw XML-RPC value
  const rawValue = response?.methodResponse?.params?.param?.value;
  // Convert the XML value to a JSON (boolean) value
  const parsedValue = xmlRpcValueToJson(rawValue);
  return parsedValue;
};

/**
 * Calls the get_single_pallets method to retrieve single palette zone IDs.
 * @returns Array of zone IDs that are single palettes
 */
export const getSinglePallets = async (): Promise<number[]> => {
  const result = await callXMLRPCMethod("get_single_pallets");
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        const rawValue = result?.methodResponse?.params?.param?.value;
        const parsed = xmlRpcValueToJson(rawValue);
        // Ensure it's an array
        const arrayResult = Array.isArray(parsed) ? parsed : [parsed];
        resolve(arrayResult);
      } catch (error) {
        reject(error);
      }
    }, 0);
  });
};
