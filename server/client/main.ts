import xmlrpc from "xmlrpc";

// ============================================================================
// Configuration
// ============================================================================

const SERVER_CONFIG = {
  host: "localhost",
  port: 9999,
  path: "/"
} as const;

const POLL_INTERVAL_MS = 1500;
const TARGET_ZONE = { current: 1, next: 2 };
const DEFAULT_ROBOT_ID = 1;

// ============================================================================
// XML-RPC Client Setup
// ============================================================================

/**
 * Creates an XML-RPC client connection to the server
 */
const xmlrpcClient = xmlrpc.createClient(SERVER_CONFIG);

/**
 * Helper function to make XML-RPC method calls and convert to Promises
 * @param method - The RPC method name to call
 * @param params - Array of parameters to pass to the method
 * @returns Promise that resolves with the method's response
 */
async function callRpcMethod(method: string, params: any[] = []): Promise<any> {
  return new Promise((resolve, reject) => {
    xmlrpcClient.methodCall(method, params, (error, value) => {
      if (error) {
        reject(error);
        return;
      }
      resolve(value);
    });
  });
}

// ============================================================================
// RPC Method Calls
// ============================================================================

/**
 * Restarts the system on the server
 */
async function restartSystem(): Promise<void> {
  console.log("🔄 Restarting system...");
  await callRpcMethod("restart");
  // const data = await callRpcMethod("get_archiv_data");
  // console.log("✅ Data:", data);
  console.log("✅ System restarted successfully");
}

/**
 * Gets the current task from the server
 * @param randomId - The random ID from previous call (0 for initial call)
 * @param robotId - The robot ID (default: 1)
 * @returns Task object containing zone information and random_id
 */
async function getTask(randomId: number = 0, robotId: number = DEFAULT_ROBOT_ID): Promise<any> {
  console.log(`📋 Getting task with randomId=${randomId}, robotId=${robotId}...`);
  const task = await callRpcMethod("get_task", [randomId, robotId]);
  console.log(`✅ Received task: curr_zone=${task.curr_zone}, next_zone=${task.next_zone}, random_id=${task.random_id}`);
  return task;
}

/**
 * Initializes a vial on the server
 * @param randomId - The random ID to track this operation
 */
async function initVial(randomId: number): Promise<void> {
  console.log(`🧪 Initializing vial with randomId=${randomId}...`);
  await callRpcMethod("init_vial", ["True", randomId]);
  console.log("✅ Vial initialized");
}

/**
 * Updates the camera 2 result on the server
 * @param randomId - The random ID to track this operation
 */
async function updateCamera2Result(randomId: number): Promise<void> {
  console.log(`📸 Updating camera 2 result with randomId=${randomId}...`);
  await callRpcMethod("update_camera2_result", ["True", "1", randomId]);
  console.log("✅ Camera 2 result updated");
}

// ============================================================================
// Main Business Logic
// ============================================================================

/**
 * Polls the server until the task reaches the target zone configuration
 * The server returns a new random_id with each response, which must be used
 * in the next call to maintain state consistency.
 * 
 * @param initialRandomId - The random ID from the initial task call
 * @returns The latest random_id when the zone condition is met
 */
async function pollUntilZoneMatch(initialRandomId: number): Promise<number> {
  console.log(`\n🔍 Polling until zone matches target: current=${TARGET_ZONE.current}, next=${TARGET_ZONE.next}\n`);

  let currentRandomId = initialRandomId;
  let pollCount = 0;

  while (true) {
    pollCount++;
    const task = await getTask(currentRandomId, DEFAULT_ROBOT_ID);

    // Update random_id from response for next iteration
    // The server generates a new random_id with each call
    if (task.random_id) {
      currentRandomId = task.random_id;
    }

    const { curr_zone, next_zone } = task;
    console.log(`[Poll #${pollCount}] Zone status: current=${curr_zone}, next=${next_zone}, random_id=${currentRandomId}`);

    // Check if we've reached the target zone configuration
    if (curr_zone === TARGET_ZONE.current && next_zone === TARGET_ZONE.next) {
      console.log("🎯 Target zone condition matched!");
      return currentRandomId;
    }

    // Wait before polling again
    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
  }
}

// ============================================================================
// Main Execution Flow
// ============================================================================

/**
 * Main function that orchestrates the XML-RPC workflow:
 * 1. Restart the system
 * 2. Get initial task to obtain random_id
 * 3. Poll until zone matches target
 * 4. Initialize vial with latest random_id
 * 5. Update camera 2 result with latest random_id
 */
async function main(): Promise<void> {
  try {
    // Step 1: Restart the system
    await restartSystem();

    // Step 2: Get initial task (use 0 as random_id for first call)
    const initialTask = await getTask(0, DEFAULT_ROBOT_ID);
    const initialRandomId = initialTask?.random_id;

    if (!initialRandomId) {
      throw new Error("Failed to get random_id from initial task response");
    }

    console.log(`\n📌 Starting workflow with random_id: ${initialRandomId}\n`);

    // Step 3: Poll until zone matches target (updates random_id each iteration)
    const latestRandomId = await pollUntilZoneMatch(initialRandomId);

    // Step 4: Initialize vial using the latest random_id
    await initVial(latestRandomId);

    // Step 5: Update camera 2 result using the latest random_id
    await updateCamera2Result(latestRandomId);

    console.log("\n🎉 XML-RPC workflow completed successfully!\n");

  } catch (error) {
    console.error("\n❌ Error occurred during workflow:", error);
    process.exit(1);
  }
}

// Execute the main workflow
main();
