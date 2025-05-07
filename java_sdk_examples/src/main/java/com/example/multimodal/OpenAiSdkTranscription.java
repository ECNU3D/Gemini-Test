package com.example.multimodal;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.audio.CreateTranscriptionRequest;
import com.theokanning.openai.audio.AudioResult; // Or TranscriptionResult, need to check SDK
import com.theokanning.openai.service.OpenAiService;

import java.io.File;
import java.time.Duration;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkTranscription {
    // Note: To run this example, you need an audio file (e.g., "test_audio.mp3" or "test_audio.wav")
    // in the root of the `java_sdk_examples` directory, or provide a correct path.
    // The audio file should be in a format supported by the OpenAI API (e.g. flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, or webm).
    private static final String AUDIO_FILE_PATH = "../sample_audio.mp3"; // Adjust if your file is elsewhere or named differently

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        // Transcription model is often specified in the request or chosen by endpoint, 
        // but some SDKs might allow setting a default model for audio tasks.
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
            System.err.println("You can often find sample audio files online for testing (e.g. search 'sample wav file download')");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Audio Transcription --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                System.out.println("Using custom API base URL: " + apiBaseUrl);
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(60)) // Longer timeout for audio upload/processing
                    .newBuilder().build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
            } else {
                System.out.println("Using default OpenAI API base URL.");
                service = new OpenAiService(apiKey, Duration.ofSeconds(60));
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        // --- Prepare Transcription Request --- 
        CreateTranscriptionRequest.Builder transcriptionRequestBuilder = CreateTranscriptionRequest.builder()
            // .language("en") // Optional: Specify language ISO-639-1 code
            // .prompt("The following audio is about...") // Optional: Provide context
            // .responseFormat("json") // Optional: "json", "text", "srt", "verbose_json", or "vtt"
            .temperature(0.2); // Optional: Sampling temperature

        if (modelName != null && !modelName.isEmpty()) {
            transcriptionRequestBuilder.model(modelName); // e.g., "whisper-1"
        } else {
            System.out.println("No transcription model specified in .env, using SDK default or endpoint default (often 'whisper-1').");
            // The SDK or endpoint will likely use a default like "whisper-1" if not specified.
            // For explicit control, ensure MODEL_NAME is set in .env for transcription.
        }
        CreateTranscriptionRequest request = transcriptionRequestBuilder.build();

        System.out.println("Sending transcription request for file: " + audioFile.getName());
        if (request.getModel() != null) {
             System.out.println("Model: " + request.getModel());
        }
        System.out.println("------------------------------------");

        try {
            // The method in the SDK is createTranscription, taking the request and the audio file path.
            AudioResult result = service.createTranscription(request, audioFile.getPath());
            // The result object (AudioResult or similar) should contain the transcribed text.
            // In older versions, it might directly be a String if responseFormat is "text".

            System.out.println("--- API Response (Transcription) --- ");
            System.out.println("Transcribed Text: " + result.getText());
            // If verbose_json or other formats are used, result object will have more fields.
            System.out.println("------------------------------------");

        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error: " + e.code() + " " + e.message());
            try {
                System.err.println("Error Body: " + (e.response().errorBody() != null ? e.response().errorBody().string() : "N/A"));
            } catch (IOException ioe) { System.err.println("Error reading error body: " + ioe); }
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("Unexpected error during transcription: " + e.getMessage());
            e.printStackTrace();
        }

        service.shutdownExecutor();
        System.out.println("SDK audio transcription example complete.");
    }
} 