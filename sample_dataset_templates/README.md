# EvalWise Dataset Templates

This directory contains sample dataset templates that demonstrate different evaluation categories for LLM testing. Each template follows a consistent CSV structure compatible with EvalWise's evaluation system.

## 📁 Available Templates

### 1. 🔴 **Jailbreak Resistance Template** (`jailbreak_resistance_template.csv`)
**Purpose**: Test model resistance to prompt injection and manipulation attempts

**Key Features**:
- Various jailbreak techniques (DAN, roleplay, fictional pretext)
- Difficulty levels (basic, intermediate, advanced) 
- Risk assessment (low, medium, high, critical)
- Expected safe responses for each attack type

**Sample Attack Types**:
- Direct instruction override
- Roleplay jailbreaking
- Fictional pretext manipulation
- Completion traps
- Instruction contradiction

### 2. 🔒 **PII Protection Template** (`pii_protection_template.csv`)
**Purpose**: Evaluate privacy protection and personal information handling

**Key Features**:
- Various PII types (SSN, email, phone, address, credit cards)
- Risk-based classification system
- Expected privacy-safe responses
- Detection capabilities testing

**Coverage Areas**:
- User PII exposure scenarios
- System information requests
- Contact information handling
- Financial data protection
- Personal information storage policies

### 3. 📊 **Content Quality Template** (`content_quality_template.csv`)
**Purpose**: Assess output quality across different task types

**Key Features**:
- Multi-domain coverage (technology, programming, creative, etc.)
- Quality scoring (0.0 to 1.0 scale)
- Specific evaluation criteria per task
- Difficulty progression

**Task Categories**:
- Summarization with constraints
- Question answering (factual)
- Code generation with error handling
- Creative writing with style requirements
- Mathematical reasoning with explanations
- Concept explanation for target audiences

### 4. ⚖️ **Bias & Fairness Template** (`bias_fairness_template.csv`)
**Purpose**: Detect and measure algorithmic bias across protected attributes

**Key Features**:
- Identical-qualification scenarios
- Multiple protected attributes (gender, race, age, etc.)
- Risk level classification
- Expected equal treatment verification

**Bias Types Covered**:
- Name-based bias (ethnic/gender names)
- Age discrimination scenarios
- Racial bias in critical decisions (medical, legal)
- Socioeconomic status bias
- Gender bias in professional contexts

### 5. 🛡️ **Adversarial Robustness Template** (`adversarial_robustness_template.csv`)
**Purpose**: Test model consistency under input perturbations

**Key Features**:
- Input variation testing
- Robustness scoring
- Attack type classification
- Consistency verification

**Perturbation Types**:
- Typos and misspellings
- Extra whitespace and formatting
- Punctuation spam
- Character substitutions
- Case variations
- Instruction injections

### 6. 🌍 **Real-World Applications Template** (`real_world_applications_template.csv`)
**Purpose**: Evaluate performance in practical use cases

**Key Features**:
- Domain-specific scenarios
- Success criteria definition
- Complexity assessment
- Professional context awareness

**Application Domains**:
- Customer service interactions
- Educational tutoring
- Healthcare information (with disclaimers)
- Technical support troubleshooting
- Creative and professional writing
- Travel and lifestyle assistance

## 🏗️ **Template Structure**

### Common Fields
All templates follow a consistent structure:

**Input Fields**:
- `input.*`: Various input parameters (prompt, context, requirements, etc.)

**Expected Output Fields**:  
- `expected.*`: Expected responses, classifications, scores, etc.

**Metadata Fields**:
- `metadata.*`: Classification information, risk levels, evaluation criteria

### Scoring System
- **Quality Scores**: 0.0 to 1.0 scale (where 1.0 is perfect)
- **Risk Levels**: low, medium, high, critical
- **Difficulty**: basic, intermediate, advanced
- **Expected Outcomes**: pass, fail, conditional, etc.

## 🚀 **Usage Instructions**

### 1. Import to EvalWise
```bash
# Upload via API
curl -X POST http://localhost:8000/datasets/{dataset_id}/items \\
  -H "Authorization: Bearer {token}" \\
  -F "file=@jailbreak_resistance_template.csv"
```

### 2. Customize Templates
- Modify existing test cases to match your use case
- Add new scenarios following the same field structure  
- Adjust difficulty levels and risk classifications
- Update expected responses for your model's behavior

### 3. Combine Templates
- Mix different template types for comprehensive evaluation
- Create custom categories by combining elements
- Adjust metadata tags for better organization

## 📝 **Template Creation Guidelines**

### For Safety/Security Templates:
1. Include both attack attempts and benign queries
2. Specify clear expected safe responses
3. Classify risk levels appropriately
4. Cover multiple attack vectors per category

### For Quality Templates:
1. Define specific evaluation criteria
2. Include examples across difficulty levels
3. Provide clear expected outputs
4. Consider domain-specific requirements

### For Bias Templates:
1. Create truly comparable scenarios
2. Identify all protected attributes
3. Specify expected equal treatment
4. Include high-stakes decision scenarios

## 🔍 **Evaluation Best Practices**

1. **Balanced Coverage**: Include both positive and negative test cases
2. **Progressive Difficulty**: Start with basic tests, advance to complex scenarios
3. **Real-World Relevance**: Base scenarios on actual usage patterns
4. **Clear Success Criteria**: Define measurable success/failure conditions
5. **Regular Updates**: Refresh templates based on new attack patterns and use cases

## 🛠️ **Extending Templates**

To create new templates:
1. Follow the established CSV structure
2. Define clear metadata categories
3. Include diverse test cases within each category
4. Validate expected outputs with domain experts
5. Test with actual LLM responses to refine expectations

---

These templates provide a solid foundation for comprehensive LLM evaluation across safety, quality, fairness, and robustness dimensions. They can be customized and extended based on specific evaluation needs and use cases.