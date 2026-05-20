const { PrivacyGuardrailAgent, PrivacyLevel } = require('./privacyGuardrail');
const StyleProfilerAgent = require('./styleProfiler');

class BoutiqueOrchestrator {
    constructor(userConfig) {
        this.privacyAgent = new PrivacyGuardrailAgent(userConfig.privacy);
        this.styleAgent = new StyleProfilerAgent();
        this.styleAgent.updateProfile(userConfig.stylePreferences);
    }

    async recommendItems(query) {
        console.log(`\n--- Processing Query: "${query}" ---`);

        // 1. Validate Query through Privacy Guardrail
        const safeQuery = this.privacyAgent.validateRequest('Orchestrator', {
            text: query,
            ...this.styleAgent.profile
        });
        
        console.log('Privacy Check: Request Anonymized/Filtered.');

        // 2. Mock Discovery (This would normally call an API)
        const mockResults = [
            { id: 1, name: 'Minimalist White Linen Shirt', brand: 'Everlane', color: 'white', price: 65 },
            { id: 2, name: 'Boho Floral Dress', brand: 'Anthropologie', color: 'multi', price: 140 },
            { id: 3, name: 'Classic Navy Blazer', brand: 'J.Crew', color: 'navy', price: 198 }
        ];

        // 3. Score Results using Style Profiler
        const recommendations = mockResults.map(item => ({
            ...item,
            matchScore: (this.styleAgent.scoreProduct(item) * 100).toFixed(1) + '%'
        })).sort((a, b) => parseFloat(b.matchScore) - parseFloat(a.matchScore));

        return recommendations;
    }
}

// Demo
const userConfig = {
    privacy: { privacyLevel: PrivacyLevel.BALANCED },
    stylePreferences: {
        preferredColors: ['white', 'navy'],
        preferredBrands: ['Everlane', 'J.Crew'],
        styles: ['minimalist', 'classic'],
        budgetRange: { min: 50, max: 250 }
    }
};

const orchestrator = new BoutiqueOrchestrator(userConfig);

orchestrator.recommendItems('I need something for a summer lunch.')
    .then(recs => {
        console.log('Top Recommendations for you:');
        recs.forEach(r => console.log(`- ${r.name} (${r.brand}) - Match: ${r.matchScore}`));
    });
