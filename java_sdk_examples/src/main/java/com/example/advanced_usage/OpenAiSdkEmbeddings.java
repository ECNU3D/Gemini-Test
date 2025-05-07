package com.example.advanced_usage;

import com.example.utils.ConfigLoader;
import com.theokanning.openai.embedding.EmbeddingRequest;
import com.theokanning.openai.embedding.Embedding;
import com.theokanning.openai.embedding.EmbeddingResult;
import com.theokanning.openai.service.OpenAiService;

import java.time.Duration;
import java.util.List;
import java.util.Arrays;

import okhttp3.OkHttpClient;
import retrofit2.Retrofit;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.theokanning.openai.client.OpenAiApi;
import static com.theokanning.openai.service.OpenAiService.*;

public class OpenAiSdkEmbeddings {

    public static void main(String[] args) {
        String apiKey = ConfigLoader.getApiKey();
        String apiBaseUrl = ConfigLoader.getApiBaseUrl();
        // Embedding model name is usually specified in the request.
        // Some endpoints might use a default if not provided, or it could be part of the URL path for older APIs.
        // For modern APIs, it's a request parameter.
        String modelName = ConfigLoader.getModelName(); // e.g., "text-embedding-ada-002"

        if ("DUMMY_API_KEY".equals(apiKey)) {
            System.err.println("API Key not configured. Please check your .env file.");
            return;
        }

        System.out.println("--- TheoKanning/openai-java SDK Embeddings Example --- ");

        OpenAiService service;
        try {
            if (apiBaseUrl != null && !apiBaseUrl.equals("https://api.openai.com/v1/") && !apiBaseUrl.isEmpty()) {
                ObjectMapper mapper = defaultObjectMapper();
                OkHttpClient client = defaultClient(apiKey, Duration.ofSeconds(30)).newBuilder().build();
                Retrofit retrofit = defaultRetrofit(client, mapper).newBuilder().baseUrl(apiBaseUrl).build();
                OpenAiApi openAiApi = retrofit.create(OpenAiApi.class);
                service = new OpenAiService(openAiApi);
                System.out.println("Using custom API base URL: " + apiBaseUrl);
            } else {
                service = new OpenAiService(apiKey, Duration.ofSeconds(30));
                System.out.println("Using default OpenAI API base URL.");
            }
        } catch (Exception e) {
            System.err.println("Error initializing OpenAiService: " + e.getMessage());
            e.printStackTrace();
            return;
        }

        List<String> textsToEmbed = Arrays.asList(
                "The quick brown fox jumps over the lazy dog.",
                "Exploring the universe, one star at a time."
        );

        EmbeddingRequest.Builder requestBuilder = EmbeddingRequest.builder()
                .input(textsToEmbed);
        
        if (modelName != null && !modelName.isEmpty()) {
            requestBuilder.model(modelName);
        } else {
            // A default model is often required if not specified.
            // "text-embedding-ada-002" is a common one.
            System.out.println("No embedding model specified in .env, using 'text-embedding-ada-002'.");
            requestBuilder.model("text-embedding-ada-002");
        }
        EmbeddingRequest request = requestBuilder.build();

        System.out.println("Requesting embeddings for " + textsToEmbed.size() + " text(s) using model: " + request.getModel());
        System.out.println("------------------------------------");

        try {
            EmbeddingResult result = service.createEmbeddings(request);

            System.out.println("--- API Response (Embeddings) --- ");
            System.out.println("Model used: " + result.getModel());
            // System.out.println("Usage: " + result.getUsage()); // Usage stats might be available

            List<Embedding> embeddings = result.getData();
            if (embeddings != null && !embeddings.isEmpty()) {
                for (int i = 0; i < embeddings.size(); i++) {
                    Embedding embedding = embeddings.get(i);
                    System.out.println("\nEmbedding for input text #" + (i + 1) + ":");
                    System.out.println("Original Text: " + textsToEmbed.get(i));
                    System.out.println("Object Type: " + embedding.getObject());
                    System.out.println("Index: " + embedding.getIndex());
                    List<Double> vector = embedding.getEmbedding();
                    System.out.println("Vector dimension: " + (vector != null ? vector.size() : "N/A"));
                    System.out.println("Vector (first 5 elements): " + 
                        (vector != null && vector.size() > 5 ? vector.subList(0, 5) + "..." : vector));
                }
            } else {
                System.out.println("No embeddings returned.");
            }
            System.out.println("------------------------------------");

        } catch (retrofit2.HttpException e) {
            System.err.println("API HTTP Error: " + e.code() + " " + e.message());
            try {
                System.err.println("Error Body: " + (e.response() != null && e.response().errorBody() != null ? e.response().errorBody().string() : "N/A"));
            } catch (IOException ioe) { System.err.println("Error reading error body: " + ioe); }
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("Unexpected error: " + e.getMessage());
            e.printStackTrace();
        }

        service.shutdownExecutor();
        System.out.println("SDK Embeddings example complete.");
    }
} 