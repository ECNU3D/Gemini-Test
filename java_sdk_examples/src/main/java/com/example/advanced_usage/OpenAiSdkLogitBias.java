package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatCompletionChoice;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.service.OpenAiService;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkLogitBias {

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Logit Bias Example --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30)).newBuilder().build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(30));
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        List<ChatMessage> messages = new ArrayList<>();
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), "What is the color of the sky on a sunny day? Try to avoid common answers."));

        // Logit bias: Increase probability of token ID for "azure" (e.g., 26583 - this ID is an EXAMPLE and will vary by model/tokenizer)
        // Decrease probability of token ID for "blue" (e.g., 5012 - EXAMPLE ID)
        // Values are from -100 to 100. Higher values make token more likely, lower values make it less likely.
        // IMPORTANT: Token IDs are model-specific. You need to find the correct token IDs for your model.
        // This is a conceptual example. Finding exact token IDs usually requires a tokenizer for the specific model.
        Map<String, Integer> logitBias = new HashMap<>();
        logitBias.put("26583", 50);  // Hypothetical token ID for "azure", strongly increase
        logitBias.put("azure", 50); // Some SDKs might allow string keys if they handle tokenization.
                                  // TheoKanning SDK 0.20.0 expects String token IDs in the map.
        logitBias.put("5012", -50); // Hypothetical token ID for "blue", strongly decrease
        logitBias.put("blue", -50); // Again, for concept.

        System.out.println("Note: Logit bias token IDs are model-specific. The IDs used here (26583, 5012) are illustrative examples.");
        System.out.println("Effective logit bias will depend on correct tokenization for the target model and SDK handling.");

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .temperature(0.7)
                .logitBias(logitBias) // Set the logit bias
                .n(1);

        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName);
        } else {
            System.out.println("No model specified, using 'gpt-3.5-turbo'.");
            requestBuilder.model("gpt-3.5-turbo");
        }
        ChatCompletionRequest request = requestBuilder.build();

        System.out.println("Sending request with logit bias...");
        System.out.println("Model: " + request.getModel());
        System.out.println("Logit Bias Applied (Conceptual): " + logitBias);
        System.out.println("------------------------------------");

        try {
            List<ChatCompletionChoice> choices = service.createChatCompletion(request).getChoices();
            System.out.println("--- API Response --- ");
            if (choices != null && !choices.isEmpty()) {
                System.out.println("Assistant Message: " + choices.get(0).getMessage().getContent());
            } else {
                 System.out.println("No choices returned.");
            }
            System.out.println("------------------------------------");

        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error: " + e.code() + " " + e.message());
             try {
                System.err.println("Error Body: " + (e.response() != null && e.response().errorBody() != null ? e.response().errorBody().string() : "N/A"));
            } catch (IOException ioe) { System.err.println("Error reading error body: " + ioe); }
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
            e.printStackTrace();
        }

        service.shutdownExecutor();
        System.out.println("SDK Logit Bias example complete.");
    }
} 