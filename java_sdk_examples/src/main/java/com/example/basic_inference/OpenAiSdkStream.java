package com.example.basic_inference;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.completion.chat.ChatCompletionChunk;
import com.theokanning.openai.completion.chat.ChatCompletionRequest;
import com.theokanning.openai.completion.chat.ChatMessage;
import com.theokanning.openai.completion.chat.ChatMessageRole;
import com.theokanning.openai.service.OpenAiService;

import io.reactivex.Flowable;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

// Imports for custom OkHttpClient and Retrofit (needed for custom base URL)
import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*; // For defaultClient, defaultObjectMapper, defaultRetrofit


public class OpenAiSdkStream {

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Streaming Chat Completion --- ");

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
                service = new OpenAiService(apiKey, Duration.ofSeconds(60)); // Longer timeout for streaming
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        List<ChatMessage> messages = new ArrayList<>();
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), "Tell me a short story about a brave robot."));

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .temperature(0.7)
                .n(1)
                .stream(true); // Enable streaming

        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName);
        } else {
            System.out.println("No model specified, using default 'gpt-3.5-turbo'.");
            requestBuilder.model("gpt-3.5-turbo");
        }
        ChatCompletionRequest request = requestBuilder.build();

        System.out.println("Sending streaming request...");
        System.out.println("Model: " + request.getModel());
        System.out.println("------------------------------------");

        try {
            Flowable<ChatCompletionChunk> flowable = service.streamChatCompletion(request);
            StringBuilder assistantResponse = new StringBuilder();

            // Blocking an_async_observable_is_usually_not_recommended in production UIs/servers,
            // but for a simple CLI demo, it's acceptable.
            // Use .subscribe() with onNext, onError, onComplete for non-blocking.
            flowable.blockingForEach(chunk -> {
                if (chunk.getChoices() != null && !chunk.getChoices().isEmpty()) {
                    ChatMessage chunkMessage = chunk.getChoices().get(0).getMessage();
                    if (chunkMessage != null && chunkMessage.getContent() != null) {
                        String content = chunkMessage.getContent();
                        System.out.print(content); // Print content as it arrives
                        assistantResponse.append(content);
                    }
                    // You can also inspect chunk.getChoices().get(0).getFinishReason() if needed
                }
            });

            System.out.println("\n------------------------------------");
            System.out.println("Full Assistant Streamed Response:");
            System.out.println(assistantResponse.toString());
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

        System.out.println("Streaming SDK example complete.");
        // The OpenAiService uses a shared ExecutorService for async operations.
        // Shutting it down explicitly can be important if the application needs to terminate cleanly,
        // especially if only streaming calls were made.
        service.shutdownExecutor();
    }
} 