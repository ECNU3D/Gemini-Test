package com.example.multimodal;

import com.example.utils.ConfigLoader;
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
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class HttpClientTranscription {

    // Note: To run this example, you need an audio file (e.g., "test_audio.mp3" or "test_audio.wav")
    // in the root of the `java_sdk_examples` directory, or provide a correct path.
    private static final String AUDIO_FILE_PATH = "../sample_audio.mp3"; // Adjust path as needed
    private static final String BOUNDARY = "Boundary-" + new Random().nextLong();

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName(); // e.g., "whisper-1"

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        File audioFile = new File(AUDIO_FILE_PATH);
        if (!audioFile.exists()) {
            System.err.println("Audio file not found: " + audioFile.getAbsolutePath());
            System.err.println("Please place a sample audio file (e.g., sample_audio.mp3) in the `java_sdk_examples` parent directory.");
            System.err.println("Or update the AUDIO_FILE_PATH variable in this script.");
            return;
        }

        System.out.println("--- Java HTTP Client Audio Transcription --- ");

        HttpClient httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        ObjectMapper objectMapper = new ObjectMapper();

        try {
            // --- Prepare Multipart Form Data Request Body ---
            Path filePath = Paths.get(audioFile.getAbsolutePath());
            String fileName = filePath.getFileName().toString();
            byte[] fileBytes = Files.readAllBytes(filePath);

            List<byte[]> multipartBody = new ArrayList<>();
            // Model part
            if (modelName != null && !modelName.isEmpty()) {
                multipartBody.add(("--" + BOUNDARY + "\r\n").getBytes());
                multipartBody.add(("Content-Disposition: form-data; name=\"model\"\r\n\r\n").getBytes());
                multipartBody.add((modelName + "\r\n").getBytes());
            } else {
                // Default to whisper-1 if not specified, as it's a common requirement
                multipartBody.add(("--" + BOUNDARY + "\r\n").getBytes());
                multipartBody.add(("Content-Disposition: form-data; name=\"model\"\r\n\r\n").getBytes());
                multipartBody.add(("whisper-1" + "\r\n").getBytes());
                System.out.println("No transcription model in .env, defaulting to 'whisper-1' for HTTP request.");
            }
            
            // File part
            multipartBody.add(("--" + BOUNDARY + "\r\n").getBytes());
            multipartBody.add(("Content-Disposition: form-data; name=\"file\"; filename=\"" + fileName + "\"\r\n").getBytes());
            multipartBody.add(("Content-Type: " + Files.probeContentType(filePath) + "\r\n\r\n").getBytes()); // Guess content type
            multipartBody.add(fileBytes);
            multipartBody.add(("\r\n").getBytes());

            // Optional: language, prompt, response_format, temperature
            // Example for response_format = text
            // multipartBody.add(("--" + BOUNDARY + "\r\n").getBytes());
            // multipartBody.add(("Content-Disposition: form-data; name=\"response_format\"\r\n\r\n").getBytes());
            // multipartBody.add(("text" + "\r\n").getBytes());

            multipartBody.add(("--" + BOUNDARY + "--\r\n").getBytes());

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(apiBaseUrl + "/audio/transcriptions"))
                    .header("Content-Type", "multipart/form-data; boundary=" + BOUNDARY)
                    .header("Authorization", "Bearer " + apiKey)
                    .POST(HttpRequest.BodyPublishers.ofByteArrays(multipartBody))
                    .timeout(Duration.ofSeconds(120)) // Longer timeout for audio
                    .build();

            System.out.println("Sending transcription request for file: " + fileName + " to " + request.uri());
            System.out.println("------------------------------------");

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            System.out.println("--- API Response --- ");
            System.out.println("Status Code: " + response.statusCode());
            System.out.println("Body: " + response.body());
            System.out.println("------------------------------------");

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                try {
                    // Assuming default response format is JSON with a "text" field
                    Map<String, Object> responseMap = objectMapper.readValue(response.body(), Map.class);
                    if (responseMap.containsKey("text")) {
                        System.out.println("Transcribed Text: " + responseMap.get("text"));
                    } else {
                        System.out.println("'text' field not found in JSON response. Full response logged above.");
                    }
                } catch (JsonProcessingException e) {
                    System.err.println("Error parsing JSON response (or response was not JSON, e.g. plain text): " + e.getMessage());
                    System.err.println("If you requested a non-JSON format like 'text', the raw body above is the result.");
                }
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("Error sending HTTP request: " + e.getMessage());
            e.printStackTrace();
            if (e instanceof InterruptedException) Thread.currentThread().interrupt();
        }

        System.out.println("HTTP client audio transcription example complete.");
    }
} 