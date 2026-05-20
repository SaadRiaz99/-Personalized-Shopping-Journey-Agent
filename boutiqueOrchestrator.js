const { PrivacyGuardrailAgent, PrivacyLevel } = require('./privacyGuardrail');
const StyleProfilerAgent = require('./styleProfiler');
const DiscoveryAgent = require('./discoveryAgent');

class BoutiqueOrchestrator {
    constructor(userConfig) {
        this.privacyAgent = new PrivacyGuardrailAgent(userConfig.privacy);
        this.styleAgent = new StyleProfilerAgent();
        this.discoveryAgent = new DiscoveryAgent();
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

        // 2. Discover Products
        const discoveredItems = await this.discoveryAgent.search(safeQuery);
        console.log(`Discovery Check: Found ${discoveredItems.length} potential items.`);

        // 3. Score Results using Style Profiler
        const recommendations = discoveredItems.map(item => ({
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
