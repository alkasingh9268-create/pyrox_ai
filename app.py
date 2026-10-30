using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

class Program
{
    static async Task Main(string[] args)
    {
        string apiKey = "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";
        string url = "https://api.groq.com/openai/v1/chat/completions";

        using var client = new HttpClient();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);

        var requestPayload = new
        {
            model = "llama-3.1-8b-instant",
            messages = new[]
            {
                new { role = "user", content = "Hello! Testing Groq from C#" }
            }
        };

        string jsonBody = JsonSerializer.Serialize(requestPayload);
        var content = new StringContent(jsonBody, Encoding.UTF8, "application/json");

        try
        {
            HttpResponseMessage response = await client.PostAsync(url, content);
            string responseString = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                Console.WriteLine("🎉 Success! Response:");
                Console.WriteLine(responseString);
            }
            else
            {
                Console.WriteLine($"❌ Error ({response.StatusCode}): {responseString}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Exception aagayi: {ex.Message}");
        }
    }
}
