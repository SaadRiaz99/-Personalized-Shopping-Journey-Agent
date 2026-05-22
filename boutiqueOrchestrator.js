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
    privacy: { 
        privacyLevel: PrivacyLevel.BALANCED,
        consents: { marketing: false, thirdPartySharing: true }
    },
    stylePreferences: {
        preferredColors: ['white', 'navy'],
        preferredBrands: ['Everlane', 'J.Crew'],
        negativePreferences: {
            colors: ['yellow'], // User hates yellow
            brands: ['ASOS']    // User dislikes ASOS
        },
        styles: ['minimalist', 'classic'],
        budgetRange: { min: 50, max: 250 }
    }
};

const orchestrator = new BoutiqueOrchestrator(userConfig);

async function runDemo() {
    // 1. Regular Recommendation
    const recs = await orchestrator.recommendItems('I need something for a summer lunch.');
    console.log('Top Recommendations for you:');
    recs.forEach(r => {
        const status = parseFloat(r.matchScore) === 0 ? '[REJECTED BY STYLE GUARD]' : `Match: ${r.matchScore}`;
        console.log(`- ${r.name} (${r.brand}) - ${status}`);
    });

    // 2. Compliance Check
    console.log('\n--- Compliance Check ---');
    const canSendEmail = orchestrator.privacyAgent.checkCompliance('marketing_email');
    console.log(`Can send marketing email? ${canSendEmail ? 'YES' : 'NO (Blocked by Privacy Agent)'}`);

    // 3. GDPR Forget Me
    console.log('\n--- GDPR Action ---');
    orchestrator.privacyAgent.forgetUser();
}

runDemo();
