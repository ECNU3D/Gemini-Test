package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.Map;
import java.util.Random;
import java.util.HashMap;

public class HttpClientBatchApi {
    private static final ObjectMapper objectMapper = new ObjectMapper();
    private static final String BOUNDARY = "Boundary-" + new Random().nextLong();

    // Placeholder for a JSONL batch input file. 
    // Each line should be a valid API request object, e.g., for /v1/chat/completions.
    // Example line: {"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello world"}]}}
    private static final String BATCH_INPUT_FILE_PATH = "../sample_batch_input.jsonl"; 

    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws IOException, InterruptedException {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl(); // Should be just the base, e.g., https://api.openai.com
                                                        // The /v1 is usually part of the specific endpoint path.

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }
        
        // Ensure the API base URL does not end with /v1 for batch API file uploads, as it uses a different path structure.
        String batchApiBase = apiBaseUrl.endsWith("/v1") ? apiBaseUrl.substring(0, apiBaseUrl.length() - 3) : apiBaseUrl;
        if (batchApiBase.endsWith("/")) {
            batchApiBase = batchApiBase.substring(0, batchApiBase.length() -1);
        }

        System.out.println("--- Java HTTP Client Batch API Example --- ");
        System.out.println("Using API Base for batch file operations: " + batchApiBase);
        System.out.println("Ensure your BATCH_INPUT_FILE_PATH (currently: " + BATCH_INPUT_FILE_PATH + ") exists and is correctly formatted.");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        File inputFile = new File(BATCH_INPUT_FILE_PATH);
        if (!inputFile.exists()) {
            System.err.println("Batch input file not found: " + inputFile.getAbsolutePath());
            System.err.println("Please create a sample JSONL file for the batch input.");
            // Create a minimal dummy file for demonstration if it doesn't exist
            try {
                String dummyLine = "{\"custom_id\": \"custom_request_001\", \"method\": \"POST\", \"url\": \"/v1/chat/completions\", \"body\": {\"model\": \"gpt-3.5-turbo\", \"messages\": [{\"role\": \"user\", \"content\": \"What is 2+2?\"}]}}\n";
                Files.writeString(Paths.get(BATCH_INPUT_FILE_PATH), dummyLine);
                System.out.println("Created a dummy batch input file: " + BATCH_INPUT_FILE_PATH);
                inputFile = new File(BATCH_INPUT_FILE_PATH); // Re-initialize file object
            } catch (IOException e) {
                System.err.println("Failed to create dummy batch input file: " + e.getMessage());
                return;
            }
        }

        // 1. Upload the batch input file
        String fileId = null;
        try {
            System.out.println("\n--- 1. Uploading Batch File ---");
            Path filePath = Paths.get(inputFile.getAbsolutePath());
            String fileName = filePath.getFileName().toString();
            byte[] fileBytes = Files.readAllBytes(filePath);

            Map<Object, Object> multipartData = new HashMap<>();
            multipartData.put("purpose", "batch");
            multipartData.put("file", filePath); // Path object for HttpClient to handle file part

            // Building a multipart/form-data request body manually is complex.
            // Using a helper or relying on HttpClient's ability to build from Path for "file" part.
            // Here, we create a simple multipart body for purpose and file.
            // NOTE: HttpClient's built-in multipart handling is limited. For robust multipart, 
            // a library or more manual construction (as in HttpClientTranscription) is better.
            // For simplicity, this might not work with all custom servers if they expect precise multipart formatting.
            
            HttpRequest.BodyPublisher_Takewhile_BodyPublisher bodyPublisher = HttpRequest.BodyPublishers.ofByteArray(buildMultipartData(Map.of("purpose", "batch"), "file", filePath, BOUNDARY));

            HttpRequest uploadRequest = HttpRequest.newBuilder()
                    .uri(URI.create(batchApiBase + "/v1/files")) // OpenAI file upload endpoint
                    .header("Authorization", "Bearer " + apiKey)
                    .header("Content-Type", "multipart/form-data; boundary=" + BOUNDARY)
                    .POST(bodyPublisher)
                    .timeout(Duration.ofSeconds(60))
                    .build();

            HttpResponse<String> uploadResponse = httpClient.send(uploadRequest, HttpResponse.BodyHandlers.ofString());
            System.out.println("Upload Response Status: " + uploadResponse.statusCode());
            System.out.println("Upload Response Body: " + uploadResponse.body());

            if (uploadResponse.statusCode() == 200) {
                Map<String, Object> uploadResponseMap = objectMapper.readValue(uploadResponse.body(), Map.class);
                fileId = (String) uploadResponseMap.get("id");
                System.out.println("File uploaded successfully. File ID: " + fileId);
            } else {
                System.err.println("File upload failed.");
                return;
            }
        } catch (Exception e) {
            System.err.println("Error during file upload: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        if (fileId == null) return;

        // 2. Create a batch job
        String batchJobId = null;
        try {
            System.out.println("\n--- 2. Creating Batch Job --- ");
            Map<String, String> batchRequestMap = new HashMap<>();
            batchRequestMap.put("input_file_id", fileId);
            batchRequestMap.put("endpoint", "/v1/chat/completions"); // The target endpoint for requests in the batch file
            batchRequestMap.put("completion_window", "24h"); // e.g., "24h"
            // Optional: metadata

            String batchRequestBodyJson = objectMapper.writeValueAsString(batchRequestMap);
            HttpRequest batchCreateRequest = HttpRequest.newBuilder()
                    .uri(URI.create(batchApiBase + "/v1/batches"))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + apiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(batchRequestBodyJson))
                    .build();

            HttpResponse<String> batchCreateResponse = httpClient.send(batchCreateRequest, HttpResponse.BodyHandlers.ofString());
            System.out.println("Batch Create Response Status: " + batchCreateResponse.statusCode());
            System.out.println("Batch Create Response Body: " + batchCreateResponse.body());
            
            if (batchCreateResponse.statusCode() == 200) {
                 Map<String, Object> batchCreateMap = objectMapper.readValue(batchCreateResponse.body(), Map.class);
                 batchJobId = (String) batchCreateMap.get("id");
                 System.out.println("Batch job created successfully. Batch ID: " + batchJobId);
            } else {
                System.err.println("Batch job creation failed.");
                return;
            }
        } catch (Exception e) {
            System.err.println("Error creating batch job: " + e.getMessage());
            e.printStackTrace();
            return;
        }
        
        if (batchJobId == null) return;

        // 3. Check batch job status (and optionally retrieve results - not fully implemented here for brevity)
        // Polling for status is required. A real implementation would poll until completion or failure.
        try {
            System.out.println("\n--- 3. Checking Batch Job Status (Example - retrieve once) ---");
            HttpRequest statusRequest = HttpRequest.newBuilder()
                    .uri(URI.create(batchApiBase + "/v1/batches/" + batchJobId))
                    .header("Authorization", "Bearer " + apiKey)
                    .GET()
                    .build();

            HttpResponse<String> statusResponse = httpClient.send(statusRequest, HttpResponse.BodyHandlers.ofString());
            System.out.println("Batch Status Response Status: " + statusResponse.statusCode());
            System.out.println("Batch Status Response Body: " + statusResponse.body());
            
            // Further steps would involve: 
            // - Polling this status endpoint until job is "completed" or "failed".
            // - If completed, the response includes an "output_file_id".
            // - Downloading the content of the "output_file_id" using the /v1/files/{file_id}/content endpoint.
            // - The output file is also a JSONL, where each line corresponds to a request and contains either a response or an error.
            System.out.println("Next steps: Poll status, then retrieve results from output_file_id if completed.");

        } catch (Exception e) {
            System.err.println("Error checking batch job status: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("\nHTTP Client Batch API example (conceptual) complete.");
    }

    // Helper method to build multipart/form-data body (simplified)
    // A proper library is usually better for robust multipart creation.
    private static byte[] buildMultipartData(Map<String, String> textParts, String filePartName, Path filePath, String boundary) throws IOException {
        List<byte[]> byteArrays = new ArrayList<>();
        for (Map.Entry<String, String> entry : textParts.entrySet()) {
            byteArrays.add(("--" + boundary + "\r\n").getBytes(StandardCharsets.UTF_8));
            byteArrays.add(("Content-Disposition: form-data; name=\"" + entry.getKey() + "\"\r\n\r\n").getBytes(StandardCharsets.UTF_8));
            byteArrays.add((entry.getValue() + "\r\n").getBytes(StandardCharsets.UTF_8));
        }

        byteArrays.add(("--" + boundary + "\r\n").getBytes(StandardCharsets.UTF_8));
        byteArrays.add(("Content-Disposition: form-data; name=\"" + filePartName + "\"; filename=\"" + filePath.getFileName().toString() + "\"\r\n").getBytes(StandardCharsets.UTF_8));
        byteArrays.add(("Content-Type: " + Files.probeContentType(filePath) + "\r\n\r\n").getBytes(StandardCharsets.UTF_8));
        byteArrays.add(Files.readAllBytes(filePath));
        byteArrays.add(("\r\n").getBytes(StandardCharsets.UTF_8));
        byteArrays.add(("--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));

        // Combine all parts
        int totalLength = 0;
        for (byte[] arr : byteArrays) {
            totalLength += arr.length;
        }
        byte[] result = new byte[totalLength];
        int destPos = 0;
        for (byte[] arr : byteArrays) {
            System.arraycopy(arr, 0, result, destPos, arr.length);
            destPos += arr.length;
        }
        return result;
    }
}
