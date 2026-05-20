/**
 * Style Profiler Agent
 * Builds and manages the user's fashion and lifestyle profile.
 */

class StyleProfilerAgent {
    constructor() {
        this.profile = {
            preferredColors: [],
            preferredBrands: [],
            styles: [], // e.g., 'minimalist', 'vintage'
            budgetRange: { min: 0, max: 1000 },
            sizePreferences: {}
        };
    }

    /**
     * Updates the profile based on user input or behavior.
     */
    updateProfile(updates) {
        Object.keys(updates).forEach(key => {
            if (Array.isArray(this.profile[key])) {
                this.profile[key] = [...new Set([...this.profile[key], ...updates[key]])];
            } else if (typeof this.profile[key] === 'object') {
                this.profile[key] = { ...this.profile[key], ...updates[key] };
            } else {
                this.profile[key] = updates[key];
            }
        });
        return this.profile;
    }

    /**
     * Scores a product based on the user's profile.
     * @returns {number} Score from 0 to 1
     */
    scoreProduct(product) {
        let score = 0;
        let totalWeights = 0;

        // Color Match (Weight: 2)
        if (product.color && this.profile.preferredColors.includes(product.color)) {
            score += 2;
        }
        totalWeights += 2;

        // Brand Match (Weight: 3)
        if (product.brand && this.profile.preferredBrands.includes(product.brand)) {
            score += 3;
        }
        totalWeights += 3;

        // Budget Match (Weight: 5)
        if (product.price >= this.profile.budgetRange.min && product.price <= this.profile.budgetRange.max) {
            score += 5;
        }
        totalWeights += 5;

        return score / totalWeights;
    }

    getProfileSummary() {
        return `Style Profile: ${this.profile.styles.join(', ')} | Colors: ${this.profile.preferredColors.join(', ')}`;
    }
}

module.exports = StyleProfilerAgent;
