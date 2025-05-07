package com.example.advanced_usage;

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
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkAdvancedStream {

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        String modelName = ConfigLoader.getModelName();

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Advanced Streaming --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(60)).newBuilder().build(); 
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(60));
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        List<ChatMessage> messages = new ArrayList<>();
        messages.add(new ChatMessage(ChatMessageRole.USER.value(), "Tell me a very long and detailed story about a futuristic city."));

        ChatCompletionRequest.Builder requestBuilder = ChatCompletionRequest.builder()
                .messages(messages)
                .temperature(0.7)
                .stream(true)
                .n(1);

        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName);
        } else {
            requestBuilder.model("gpt-3.5-turbo");
        }
        ChatCompletionRequest request = requestBuilder.build();

        System.out.println("Sending advanced streaming request...");
        System.out.println("------------------------------------");

        StringBuilder fullResponse = new StringBuilder();
        CountDownLatch latch = new CountDownLatch(1); // To wait for stream completion in this demo
        AtomicBoolean streamHadError = new AtomicBoolean(false);

        try {
            Flowable<ChatCompletionChunk> flowable = service.streamChatCompletion(request);

            flowable.subscribe(
                chunk -> {
                    // Process each chunk
                    if (chunk.getChoices() != null && !chunk.getChoices().isEmpty()) {
                        ChatMessage messageDelta = chunk.getChoices().get(0).getMessage();
                        if (messageDelta != null && messageDelta.getContent() != null) {
                            String content = messageDelta.getContent();
                            System.out.print(content); // Print content as it arrives
                            fullResponse.append(content);
                        }
                        // Note: TheoKanning SDK 0.20.0 ChatCompletionChunk might not expose detailed usage/token counts per chunk
                        // or specific 'finish_details' beyond 'finish_reason' in the last chunk's delta if applicable.
                        String finishReason = chunk.getChoices().get(0).getFinishReason();
                        if(finishReason != null){
                             System.out.println("\nFinish Reason received: " + finishReason);
                        }
                    }
                     // Check for other potential fields in the chunk if the API sends them (e.g. usage, errors)
                    // However, this SDK version primarily focuses on content deltas in chunks.
                },
                error -> {
                    // Handle stream-level errors (e.g., network issues during streaming)
                    System.err.println("\n--- Stream Error --- ");
                    if (error instanceof retrofit2.HttpException) {
                        retrofit2.HttpException httpError = (retrofit2.HttpException) error;
                        System.err.println("API HTTP Error: " + httpError.code() + " " + httpError.message());
                        try {
                            String errorBody = httpError.response().errorBody() != null ? httpError.response().errorBody().string() : "No error body";
                            System.err.println("Error Body: " + errorBody);
                        } catch (Exception e) {
                            System.err.println("Could not parse error body: " + e.getMessage());
                        }
                    } else {
                        System.err.println("Streaming error: " + error.getMessage());
                    }
                    // error.printStackTrace();
                    streamHadError.set(true);
                    latch.countDown(); // Release latch on error
                },
                () -> {
                    // Handle stream completion
                    System.out.println("\n--- Stream Completed --- ");
                    latch.countDown(); // Release latch on completion
                }
            );

            // Wait for the stream to complete or timeout
            if (!latch.await(2, TimeUnit.MINUTES)) { // Timeout for the whole stream
                System.err.println("\nStream processing timed out.");
                streamHadError.set(true);
            }

        } catch (Exception e) { // Errors initiating the stream (e.g., connection refused before stream starts)
            System.err.println("Error initiating stream request: " + e.getMessage());
            streamHadError.set(true);
            // e.printStackTrace();
        }
        
        System.out.println("------------------------------------");
        if (!streamHadError.get()) {
            System.out.println("Full Streamed Response:");
            System.out.println(fullResponse.toString());
        } else {
            System.out.println("Stream encountered errors or timed out. Full response might be incomplete.");
            System.out.println("Partial response (if any):\n" + fullResponse.toString());
        }
        System.out.println("------------------------------------");

        service.shutdownExecutor();
        System.out.println("SDK Advanced Streaming example complete.");
    }
} 