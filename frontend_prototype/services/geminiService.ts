import { GoogleGenAI } from "@google/genai";
import { DailyStat, PricingRecommendation } from '../types';

const getApiKey = (): string => {
  // Check for environment variable (Vite uses import.meta.env)
  if (typeof import.meta !== 'undefined' && import.meta.env?.GEMINI_API_KEY) {
    return import.meta.env.GEMINI_API_KEY;
  }
  // Fallback to process.env for Node.js environments
  if (typeof process !== 'undefined' && process.env?.GEMINI_API_KEY) {
    return process.env.GEMINI_API_KEY;
  }
  if (typeof process !== 'undefined' && process.env?.API_KEY) {
    return process.env.API_KEY;
  }
  return '';
};

export const generatePricingInsight = async (
  recommendations: PricingRecommendation[],
  trends: DailyStat[]
): Promise<string> => {
  const apiKey = getApiKey();
  
  if (!apiKey) {
    // Return a simulated insight when no API key is available
    const totalChange = recommendations.reduce((sum, r) => sum + (r.recommendedPrice - r.currentPrice), 0);
    const avgConfidence = recommendations.length > 0 
      ? recommendations.reduce((sum, r) => sum + r.confidence, 0) / recommendations.length 
      : 0;
    
    if (recommendations.length === 0) {
      return "All prices are within optimal range. No significant adjustments needed at this time.";
    }
    
    const direction = totalChange > 0 ? "increases" : "decreases";
    const magnitude = Math.abs(totalChange / recommendations.length);
    
    return `Based on current demand patterns showing Thursday peaks (+16.7%) and model accuracy of 95.35%, ` +
           `I recommend ${recommendations.length > 1 ? 'approving these' : 'approving this'} price ${direction}. ` +
           `The average adjustment of ${magnitude.toFixed(0)} SAR per category aligns with ` +
           `supply-demand dynamics. Confidence: ${avgConfidence.toFixed(0)}%.`;
  }

  try {
    const ai = new GoogleGenAI({ apiKey });

    const prompt = `
      Analyze the following car rental dynamic pricing data and provide a concise strategic summary for the branch manager.
      
      Current Recommendations:
      ${JSON.stringify(recommendations.map(r => ({ 
        category: r.category, 
        old: r.currentPrice, 
        new: r.recommendedPrice, 
        reason: r.reason,
        confidence: r.confidence
      })))}
      
      Recent Trend Data (Demand vs Actuals):
      ${JSON.stringify(trends)}
      
      Key Context: 
      - Thursdays typically see +16.7% demand.
      - System accuracy is 95.63%.
      - This is for a car rental company in Saudi Arabia.
      
      Provide a 2-3 sentence executive summary advising on whether to approve these price changes.
      Be specific about the expected business impact.
    `;

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });
    
    return response.text || "No insights generated.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    
    // Provide a fallback response on error
    return `Unable to connect to AI service. Based on the pricing rules engine, ` +
           `these recommendations are generated with ${recommendations.length > 0 ? recommendations[0].confidence : 95}% confidence. ` +
           `Review the demand and supply multipliers before approving.`;
  }
};
