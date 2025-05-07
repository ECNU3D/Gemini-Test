package com.example.basic_inference;

import com.example.utils.ConfigLoader;
// Imports for TheoKanning/openai-java SDK
import com.theokanning.openai.service.OpenAiService;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.completion.chat.ChatCompletionChoice;
// The TheoKanning library typically wraps Retrofit exceptions or uses its own.
// For simplicity, we'll catch a general Exception for API errors first.
// import com.theokanning.openai.OpenAiHttpException; // Or similar if it exists

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.time.Duration;

// Import for custom OkHttpClient and Retrofit (needed for custom base URL)
import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*; // For defaultClient, defaultObjectMapper, defaultRetrofit

public class OpenAiSdkNormal {

    public static void main(String[] args) {
        // Load configuration
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName(); // Renamed for clarity

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Normal Chat Completion --- ");

        // --- Initialize OpenAiService --- 
        // IMPORTANT: For custom base URLs (like http://localhost:8000/v1),
        // the TheoKanning/openai-java library requires a custom OkHttpClient and Retrofit setup.
        // The default constructor OpenAiService(String token) uses the official OpenAI base URL.

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                System.out.println("Using custom API base URL: " + apiBaseUrl);
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30)) // Default timeout, can be configured
                    .newBuilder()
                    // Add proxy or other interceptors if needed here
                    .build();
                Retrofit retrofit = defaultRetrofit(client, mapper)
                    .newBuilder()
                    .baseUrl(apiBaseUrl) // Set the custom base URL here
                    .build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
            } else {
                System.out.println("Using default OpenAI API base URL.");
                service = new OpenAiService(apiKey, Duration.ofSeconds(30)); // Timeout can be adjusted
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService with custom base URL: " + e.getMessage());
            System.err.println("Ensure your custom base URL is correct and the server is accessible.");
            e.printStackTrace();
            return;
        }

        // --- Prepare API Request --- 
        List<ChatMessage> messages = new ArrayList<>();
        // Use ChatMessageRole enum for roles
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), "What is the capital of France?"));

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .temperature(0.7)
                // .maxTokens(50) // Optional
                .n(1); // Number of choices to generate

        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName);
        } else {
            // Fallback to a default model if none is configured, as 'model' is required by the SDK
            // This default might need adjustment based on the compatible endpoint's requirements.
            System.out.println("No model specified in .env, using default 'gpt-3.5-turbo' for SDK request.");
            requestBuilder.model("gpt-3.5-turbo"); 
        }
        ChatCompletionRequest request = requestBuilder.build();

        System.out.println("Sending request...");
        System.out.println("Model: " + request.getModel());
        System.out.println("Messages: " + request.getMessages().stream().map(m -> m.getRole() + ": " + m.getContent()).collect(Collectors.joining("\n")) );
        System.out.println("------------------------------------");

        try {
            // --- Send Request & Get Response --- 
            // The method is createChatCompletion, not getChatCompletions
            List<ChatCompletionChoice> choices = service.createChatCompletion(request).getChoices();

            System.out.println("--- Full API Response (Choices) --- ");
            if (choices != null && !choices.isEmpty()) {
                for (ChatCompletionChoice choice : choices) {
                    System.out.println("Choice Index: " + choice.getIndex());
                    System.out.println("Finish Reason: " + choice.getFinishReason());
                    if (choice.getMessage() != null) {
                        System.out.println("Assistant Message: " + choice.getMessage().getContent());
                        System.out.println("Role: " + choice.getMessage().getRole());
                    } else {
                        System.out.println("No message object in this choice.");
                    }
                    System.out.println("---");
                }
                // Typically, you'd use the first choice:
                // ChatMessage assistantMessage = choices.get(0).getMessage();
                // System.out.println("Primary Assistant Message: " + assistantMessage.getContent());

            } else {
                 System.out.println("No choices returned in the response.");
            }
            // The full response object also contains id, model, usage, etc., but getChoices() is common.
            // Example: com.theokanning.openai.completion.chat.ChatCompletionResult result = service.createChatCompletion(request);
            // System.out.println("Response ID: " + result.getId());
            // System.out.println("Usage: " + result.getUsage());

            System.out.println("------------------------------------");

        // TheoKanning library might throw a retrofit2.HttpException for API errors
        // or a more specific com.theokanning.openai.OpenAiHttpException. 
        // For broader compatibility with older versions or variations, catch general Exception.
        } catch (retrofit2.HttpException e) { // More specific for HTTP errors
            System.err.println("API HTTP Error occurred: " + e.code() + " " + e.message());
            try {
                String errorBody = e.response().errorBody() != null ? e.response().errorBody().string() : "No error body";
                System.err.println("Error Body: " + errorBody);
            } catch (Exception ioException) {
                System.err.println("Could not parse error body: " + ioException.getMessage());
            }
            e.printStackTrace();
        } catch (Exception e) { // Catch-all for other issues
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("TheoKanning SDK example complete.");
        // Important for streaming examples, but good practice to include if using OpenAiService with background executor.
        // service.shutdownExecutor(); 
    }
} 