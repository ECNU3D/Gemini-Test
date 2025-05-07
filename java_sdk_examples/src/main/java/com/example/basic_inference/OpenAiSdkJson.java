package com.example.basic_inference;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatCompletionChoice;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.completion.chat.ChatCompletionRequest.ChatCompletionRequestFunctionCall;
import com.theokanning.openai.service.OpenAiService;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

// Imports for custom OkHttpClient and Retrofit (needed for custom base URL)
import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkJson {

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK JSON Mode Chat Completion --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                System.out.println("Using custom API base URL: " + apiBaseUrl);
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30))
                    .newBuilder()
                    .build();
                Retrofit retrofit = defaultRetrofit(client, mapper)
                    .newBuilder()
                    .baseUrl(apiBaseUrl)
                    .build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
            } else {
                System.out.println("Using default OpenAI API base URL.");
                service = new OpenAiService(apiKey, Duration.ofSeconds(30));
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        List<ChatMessage> messages = new ArrayList<>();
        messages.add(new ChatMessage(ChatMessageRole.SYSTEM.value(), "You are a helpful assistant designed to output JSON."));
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), "Provide a JSON object with two keys: 'name' and 'city', for a fictional character."));

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .temperature(0.7)
                .n(1);
                // For JSON mode, the API typically expects a `response_format` parameter.
                // The TheoKanning SDK might not have a direct setter for `response_format` in ChatCompletionRequest.builder().
                // It might be set via a generic parameter map or might require a newer SDK version / different method.
                // For now, we proceed without explicitly setting it, relying on the system message and prompt structure.
                // If the specific endpoint *requires* `{"type": "json_object"}`, this might not work as expected
                // and would need a way to add arbitrary top-level parameters to the request, or SDK update.
                // requestBuilder.responseFormat(Map.of("type", "json_object")); // Hypothetical setter

        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName);
        } else {
            System.out.println("No model specified, using default 'gpt-3.5-turbo'. This model should support JSON mode if prompted correctly.");
            requestBuilder.model("gpt-3.5-turbo"); // Or a model known to be good with JSON output
        }
        ChatCompletionRequest request = requestBuilder.build();

        System.out.println("Sending JSON mode request...");
        System.out.println("Model: " + request.getModel());
        System.out.println("Messages: " + request.getMessages().stream().map(m -> m.getRole() + ": " + m.getContent()).collect(Collectors.joining("\n")) );
        System.out.println("------------------------------------");

        try {
            List<ChatCompletionChoice> choices = service.createChatCompletion(request).getChoices();

            System.out.println("--- API Response (JSON Mode Attempt) --- ");
            if (choices != null && !choices.isEmpty()) {
                ChatMessage assistantMessage = choices.get(0).getMessage();
                String responseContent = assistantMessage.getContent();
                System.out.println("Assistant Message (Raw):\n" + responseContent);

                // Attempt to parse as JSON to verify
                try {
                    ObjectMapper jsonParser = new ObjectMapper();
                    Object jsonObj = jsonParser.readValue(responseContent, Object.class); // Parses into a generic Map/List structure
                    System.out.println("Successfully parsed as JSON:");
                    System.out.println(jsonParser.writerWithDefaultPrettyPrinter().writeValueAsString(jsonObj));
                } catch (JsonProcessingException e) {
                    System.err.println("Could not parse assistant message as JSON: " + e.getMessage());
                    System.err.println("The model might not have returned valid JSON despite the prompt.");
                }
            } else {
                 System.out.println("No choices returned in the response.");
            }
            System.out.println("------------------------------------");

        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error occurred: " + e.code() + " " + e.message());
            try {
                String errorBody = e.response().errorBody() != null ? e.response().errorBody().string() : "No error body";
                System.err.println("Error Body: " + errorBody);
            } catch (Exception ioException) {
                System.err.println("Could not parse error body: " + ioException.getMessage());
            }
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("SDK JSON mode example complete.");
        service.shutdownExecutor();
    }
} 