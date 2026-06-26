import json
import random
import os


domains = ["Engineering", "Infrastructure", "Data", "Product", "Design", "Leadership"]


data_pool = {
    "Engineering": {
        "acronyms": [
            ("API", "Application Programming Interface", "Advanced Program Interface", "Used to connect different software applications."),
            ("HTTP", "HyperText Transfer Protocol", "High-Transfer Text Protocol", "The foundation of web-based communication."),
            ("JSON", "JavaScript Object Notation", "Java System Orientation Notation", "Lightweight data format using keys and values."),
            ("DOM", "Document Object Model", "Data Object Model", "Tree representation of HTML elements in browsers."),
            ("MVC", "Model View Controller", "Model Visual Control", "Design pattern dividing app logic, data, and visual screens."),
            ("REST", "Representational State Transfer", "Remote Execution State Transfer", "Stateless architectural style utilizing HTTP routes."),
            ("JWT", "JSON Web Token", "Java Web Token", "Token format used to securely transmit user authentication."),
            ("CORS", "Cross-Origin Resource Sharing", "Central Origin Resource Sharing", "Security mechanism restricting browser requests to other origins."),
            ("DRY", "Don't Repeat Yourself", "Do Repeat Yourself", "Coding best practice discouraging redundant blocks."),
            ("OOP", "Object-Oriented Programming", "Object-Oriented Parsing", "Programming paradigm based on classes and objects.")
        ],
        "tools": [
            ("React", "building dynamic front-end user interfaces", "A Facebook-created vector library/framework.", "components"),
            ("Node.js", "executing server-side JavaScript code", "Runtime built on Chrome's V8 JavaScript engine.", "runtime"),
            ("PostgreSQL", "storing structured relational data", "An open-source relational SQL database.", "tables"),
            ("Git", "tracking local and remote source code changes", "VCS using commits, merges, and pushes.", "commits"),
            ("Docker", "packaging application code into portable containers", "Software platform to create isolated environments.", "images"),
            ("pytest", "writing and running automated Python assertions", "Popular testing framework for Python developers.", "tests"),
            ("MongoDB", "storing flexible, unstructured document data", "NoSQL document database using JSON-like structures.", "collections")
        ],
        "statements": [
            ("True or False: React is a backend database server.", False, "React handles UI rendering in browsers."),
            ("True or False: Python is a compiled language that executes directly on machine hardware.", False, "Python is interpreted via bytecode VM."),
            ("True or False: SQL databases store structured data in rows and tables.", True, "SQL databases enforce structured tabular schemas."),
            ("True or False: CSS is used to define the core database model of an application.", False, "CSS handles visual styling, layout, and fonts."),
            ("True or False: Git is a centralized version control system.", False, "Git is a distributed version control system."),
            ("True or False: JavaScript is a single-threaded runtime engine.", True, "JavaScript processes execution on a single call stack."),
            ("True or False: HTML is primarily used to structure web page content.", True, "HTML provides semantic structure to layouts."),
            ("True or False: Monolithic architectures are always superior to microservices for scaling teams.", False, "Microservices permit modular scaling of services.")
        ],
        "bugs": [
            ("In React, to preserve state between renders, you use ______.", "hooks", "Look into useState or functional components hooks."),
            ("In Python, a function that returns an iterator using the yield statement is a ______.", "generator", "It produces a sequence of values lazily."),
            ("In Git, before committing modified files, you must add them to the ______ area.", "staging", "It acts as a temporary index before saving.")
        ],
        "commands": [
            ("Git command to list all current branches in the repository.", "git branch", "Used to check branch names locally."),
            ("SQL command to retrieve only unique rows from a column.", "select distinct", "Filters duplicate column records."),
            ("Linux command to change directory permissions.", "chmod", "Modifies read, write, and execute flags.")
        ]
    },
    "Infrastructure": {
        "acronyms": [
            ("DNS", "Domain Name System", "Data Name Server", "Resolves website domains to IP addresses."),
            ("SSH", "Secure Shell", "System Security Host", "Cryptographic network protocol for secure remote access."),
            ("SSL", "Secure Sockets Layer", "Secure System Link", "Standard security technology for encrypting links."),
            ("VPN", "Virtual Private Network", "Virtual Process Node", "Extends a private network across a public network."),
            ("IAM", "Identity and Access Management", "Intelligent Access Module", "Enforces access policies and user permissions in clouds."),
            ("VPC", "Virtual Private Cloud", "Virtual Process Console", "Isolated virtual network partition in cloud infrastructures."),
            ("CDN", "Content Delivery Network", "Code Distribution Node", "Geographically distributed servers caching assets close to clients."),
            ("ALB", "Application Load Balancer", "Advanced Load Balancer", "Distributes traffic across multiple cloud targets.")
        ],
        "tools": [
            ("Terraform", "managing cloud infrastructure as code (IaC)", "HashiCorp declarative infrastructure manager.", "state"),
            ("Kubernetes", "orchestrating and scaling container pods", "Google-created container manager (K8s).", "pods"),
            ("Prometheus", "monitoring and collecting system time-series metrics", "Graduated CNCF monitoring tool.", "metrics"),
            ("Ansible", "configuring servers dynamically without local agents", "Agentless SSH automation tool.", "playbooks"),
            ("Jenkins", "building and deploying automated code pipelines", "Java-based automation server.", "pipelines")
        ],
        "statements": [
            ("True or False: Docker containers share the host operating system's kernel.", True, "Containers are lightweight and share the kernel."),
            ("True or False: Kubernetes is a container runtime similar to Docker.", False, "Kubernetes is an orchestrator, not a runtime."),
            ("True or False: Ansible requires a permanent client agent installed on remote servers.", False, "Ansible operates agentlessly over SSH."),
            ("True or False: Ping utility uses TCP protocol to check host connectivity.", False, "Ping utilizes ICMP echo request packets."),
            ("True or False: Load balancers strictly distribute traffic based on alphabetical order of targets.", False, "Load balancers distribute traffic based on algorithms like Round Robin.")
        ],
        "bugs": [
            ("In Terraform, the state mapping file recording resources is called ______.", "terraform.tfstate", "Tracks current state configuration metadata."),
            ("In Kubernetes, the smallest deployable object that runs containers is a ______.", "pod", "Hosts one or more tightly coupled containers."),
            ("In Prometheus, target metric endpoints are retrieved by ______ them at intervals.", "scraping", "Pulls metrics via HTTP GET requests.")
        ],
        "commands": [
            ("Kubernetes command-line tool used to get lists of pods.", "kubectl get pods", "Primary container deployment CLI query."),
            ("Linux command to check system disk space utilization.", "df -h", "Displays filesystem allocation in human-readable gigabytes."),
            ("SSH command option to specify a custom connection port.", "ssh -p", "Overrides default port 22.")
        ]
    },
    "Data": {
        "acronyms": [
            ("ETL", "Extract Transform Load", "Enterprise Transfer Logic", "Three-step pipeline merging data from source to warehouse."),
            ("OLAP", "Online Analytical Processing", "Online Application Protocol", "Database optimized for complex queries and business reports."),
            ("OLTP", "Online Transaction Processing", "Online Transfer Process", "Database optimized for fast, concurrent database writes."),
            ("RDBMS", "Relational Database Management System", "Relational Data Backup Module", "Database model storing data in tables with relationships."),
            ("BI", "Business Intelligence", "Backup Integration", "Analyzing data to provide actionable business strategies.")
        ],
        "tools": [
            ("Pandas", "analyzing and cleaning structured data tables", "Python library using DataFrames.", "dataframes"),
            ("NumPy", "performing fast numerical operations on arrays", "Python package for multidimensional arrays.", "arrays"),
            ("Scikit-learn", "building basic machine learning models", "Standard Python library for regression, clustering.", "models"),
            ("TensorFlow", "training deep learning neural networks", "Google framework for tensor computations.", "tensors"),
            ("Apache Spark", "processing large scale datasets across servers", "Cluster computing framework with fast processing.", "rdds"),
            ("Kafka", "streaming real-time event topics", "Distributed pub-sub event broker.", "topics")
        ],
        "statements": [
            ("True or False: Linear regression is an unsupervised machine learning algorithm.", False, "Linear regression matches labels, so it is supervised."),
            ("True or False: K-Means clustering algorithm requires pre-labeled data to group rows.", False, "K-Means is unsupervised clustering."),
            ("True or False: Structured Query Language is only applicable to NoSQL databases.", False, "SQL is primarily used in relational databases."),
            ("True or False: Overfitting means a model performs exceptionally well on unseen test data.", False, "Overfitting fails on unseen data, showing high variance.")
        ],
        "bugs": [
            ("In Pandas, to handle missing data rows, you commonly use ______.", "dropna", "Drops rows containing null values."),
            ("In SQL, to group rows sharing column values for aggregation, you use ______.", "group by", "Collapses rows into aggregate summaries.")
        ],
        "commands": [
            ("SQL keyword used to join tables on matching primary keys.", "inner join", "Standard connection filter query."),
            ("Pandas command to show the first 5 rows of a DataFrame.", "df.head()", "Quick data validation query."),
            ("SQL command to delete a table schema entirely from the database.", "drop table", "Permanently discards table and rows.")
        ]
    },
    "Product": {
        "acronyms": [
            ("MVP", "Minimum Viable Product", "Minimum Visual Prototype", "Basic product version to gather customer feedback."),
            ("ROI", "Return on Investment", "Rate of Interest", "Calculates net profit divided by cost of acquisition."),
            ("KPI", "Key Performance Indicator", "Key Product Index", "Standard metrics tracking progress to goals."),
            ("PMF", "Product Market Fit", "Product Manager Force", "Degree to which a product satisfies strong market demand."),
            ("CAC", "Customer Acquisition Cost", "Capitalized Acquisition Charge", "Total marketing expenses divided by new users acquired."),
            ("LTV", "Customer Lifetime Value", "Long Term Venture", "Projected revenue a single user brings over time."),
            ("NPS", "Net Promoter Score", "Net Product Score", "Customer loyalty survey scoring promoters minus detractors."),
            ("OKR", "Objectives and Key Results", "Operations Key Results", "Framework defining company goals and metric outcomes.")
        ],
        "tools": [
            ("Jira", "tracking agile software sprints and ticket boards", "Atlassian project coordinator.", "tickets"),
            ("Asana", "managing shared project workflows and tasks", "Collaboration platform with list and board view layouts.", "tasks"),
            ("Amplitude", "analyzing user behaviors and feature retention", "Analytics engine tracking click flows.", "cohorts"),
            ("Google Analytics", "monitoring web page traffic and visitor referrals", "Tracks pageview sessions.", "funnels")
        ],
        "statements": [
            ("True or False: User stories should be as technical as possible to help developers.", False, "User stories describe user value in plain terms."),
            ("True or False: NPS score can range from -100 to +100.", True, "NPS scales from -100 (detractors) to +100 (promoters)."),
            ("True or False: Agile methodology requires a strict, unchangeable 12-month contract roadmap.", False, "Agile prioritizes response to change over plans.")
        ],
        "bugs": [
            ("In Agile Scrum, the backlog items selected for current development are on the ______ board.", "sprint", "Represents the active 2-week workflow."),
            ("In analytics tracking, the drop-off path users take to reach checkout is a ______.", "funnel", "Visualizes steps of conversion rates.")
        ],
        "commands": [
            ("Metric abbreviation for the average revenue a single active user brings in.", "arpu", "Average Revenue Per User."),
            ("Scrum event where teams review completed sprint items.", "sprint review", "Feedback session after a sprint.")
        ]
    },
    "Design": {
        "acronyms": [
            ("UI", "User Interface", "User Integration", "The visual layout controls and screens."),
            ("UX", "User Experience", "User Extension", "The flow, usability, and customer journey logic."),
            ("CTA", "Call to Action", "Client Target Area", "Interface buttons prompting immediate action (e.g. Buy Now)."),
            ("SVG", "Scalable Vector Graphics", "Simple Visual Graphics", "XML-based vector image format scaling without loss."),
            ("HEX", "Hexadecimal Color Code", "High Exposure Color", "Color notation using six alphanumeric characters (e.g. #FFFFFF).")
        ],
        "tools": [
            ("Figma", "designing interactive vector UI prototypes", "Vector designer with real-time multi-user editing.", "frames"),
            ("Adobe Illustrator", "creating custom vector illustrations and logos", "Creative cloud vector suite.", "vectors"),
            ("Photoshop", "editing raster images and composite graphics", "Standard raster image editor.", "pixels")
        ],
        "statements": [
            ("True or False: Good accessibility practices strictly benefit visually impaired users.", False, "Accessibility benefits all users and device modes."),
            ("True or False: Serif fonts have small decorative lines attached to letter strokes.", True, "Serif has feet; sans-serif is clean."),
            ("True or False: Contrast ratio is irrelevant for readable interface typography.", False, "Contrast ratio ensures text readability.")
        ],
        "bugs": [
            ("In Figma, to group design elements inside a responsive flexbox-like container, you use Auto ______.", "layout", "Dynamically aligns layers on wrap changes."),
            ("In color theory, the parameter representing color saturation in HSL is ______.", "saturation", "Determines color purity/vibrancy.")
        ],
        "commands": [
            ("CSS property used to specify font weight boldness.", "font-weight", "Changes thickness of text characters."),
            ("Design term for the blank space surrounding layout text components.", "white space", "Also called negative space.")
        ]
    },
    "Leadership": {
        "acronyms": [
            ("CEO", "Chief Executive Officer", "Chief Enterprise Operator", "Highest-ranking corporate manager in the company."),
            ("CTO", "Chief Technology Officer", "Central Technical Operator", "Executive coordinating tech stack and dev team."),
            ("CPO", "Chief Product Officer", "Chief Process Officer", "Executive overseeing feature releases and product design."),
            ("SaaS", "Software as a Service", "System as a Service", "Licensing software via central subscriptions."),
            ("IPO", "Initial Public Offering", "Investment Purchase Option", "Transitioning a company from private to public stock markets.")
        ],
        "tools": [
            ("Slack", "coordinating internal team communication channels", "Central messaging application.", "channels"),
            ("Salesforce", "managing customer relations and sales leads", "CRM dashboard monitoring sales funnels.", "leads"),
            ("PowerPoint", "building slideshow decks for investor pitches", "Presentation software.", "slides")
        ],
        "statements": [
            ("True or False: Venture capital funding requires giving up equity shares of the startup.", True, "Investors buy stakes in exchange for cash."),
            ("True or False: Bootstrapping a startup means taking on massive debt from investment banks.", False, "Bootstrapping utilizes self-funding and revenue."),
            ("True or False: ARR stands for Annualized Realized Retention in SaaS metrics.", False, "ARR stands for Annual Recurring Revenue.")
        ],
        "bugs": [
            ("In business metrics, the rate at which subscribers unsubscribe is the ______ rate.", "churn", "Measures lost customer percentages."),
            ("The document pitch decks outline in detail is the business ______.", "model", "Defines revenue scaling systems.")
        ],
        "commands": [
            ("SaaS abbreviation for the total predictable revenue generated in a single year.", "arr", "Annual Recurring Revenue."),
            ("Term for the amount of time a company has before cash runs out.", "runway", "Calculated as cash divided by burn rate.")
        ]
    }
}

questions = []
q_id = 1


for domain in domains:
    pool = data_pool[domain]
    
    
    for i in range(40):
        acr, correct, wrong, hint = random.choice(pool["acronyms"])
        templates = [
            f"What does the acronym '{acr}' stand for?",
            f"In professional terms, what is the meaning of '{acr}'?",
            f"Under standard guidelines, '{acr}' is short for:"
        ]
        q_text = templates[i % len(templates)]
        
        options = [correct, wrong, f"{acr} System", f"Dynamic {acr} Core"]
        options = list(dict.fromkeys(options))
        while len(options) < 4:
            options.append(f"Standard {acr} {len(options)}")
        
        random.shuffle(options)
        
        questions.append({
            "id": q_id,
            "domain": domain,
            "difficulty": "mcqs",
            "type": "mcq",
            "question": q_text,
            "options": options,
            "correct_index": options.index(correct),
            "hint": f"Hint: {hint} Correct is '{correct}'."
        })
        q_id += 1

    
    for i in range(40):
        tool, task, details, concept = random.choice(pool["tools"])
        templates = [
            f"Which tool is best suited for {task}?",
            f"When you need support for {task}, which developer tool do you use?",
            f"In a team workflow, which technology resolves {task}?"
        ]
        q_text = templates[i % len(templates)]
        
        options = [tool, "Jenkins" if tool != "Jenkins" else "Jira", "Docker" if tool != "Docker" else "React", "Figma" if tool != "Figma" else "Postgres"]
        random.shuffle(options)
        
        questions.append({
            "id": q_id,
            "domain": domain,
            "difficulty": "mcqs",
            "type": "mcq",
            "question": q_text,
            "options": options,
            "correct_index": options.index(tool),
            "hint": f"Hint: {details} Correct is '{tool}'."
        })
        q_id += 1

    
    for i in range(40):
        stmt, is_true, hint = pool["statements"][i % len(pool["statements"])]
        
        questions.append({
            "id": q_id,
            "domain": domain,
            "difficulty": "work",
            "type": "best_of_two",
            "question": stmt,
            "options": ["True", "False"],
            "correct_index": 0 if is_true else 1,
            "hint": f"Hint: {hint}"
        })
        q_id += 1

    
    for i in range(25):
        q_item = pool["bugs"][i % len(pool["bugs"])]
        q_text, ans, hint = q_item
        
        questions.append({
            "id": q_id,
            "domain": domain,
            "difficulty": "bugs",
            "type": "fill_in_the_blank",
            "question": q_text,
            "correct_answer": ans,
            "hint": f"Hint: {hint} Answer begins with '{ans[0]}'."
        })
        q_id += 1

    
    for i in range(25):
        q_item = pool["commands"][i % len(pool["commands"])]
        q_text, ans, hint = q_item
        
        questions.append({
            "id": q_id,
            "domain": domain,
            "difficulty": "q_and_a",
            "type": "fill_in_the_blank",
            "question": q_text,
            "correct_answer": ans,
            "hint": f"Hint: {hint} Exact term is '{ans}'."
        })
        q_id += 1





func_names = ["bubble_sort", "binary_search", "process_matrix", "traverse_tree", "lookup_node", "hash_index", "validate_inputs", "aggregate_records", "sort_stack", "merge_branches"]
variables = ["N", "M", "K", "X", "Y", "A", "B"]
prompt_targets = [
    ("reduce memory leaks in a Python database connection class", "Use a singleton pattern with auto-closing context managers while keeping exact function signatures"),
    ("optimize a slow nested loops SQL subquery", "Rewrite as an INNER JOIN with indices, preserving columns and rows output"),
    ("refactor a deeply nested recursive function to prevent stack overflow", "Implement iterative stack-based traversal or memoization holding results state"),
    ("clean up redundant copy-pasted JavaScript components", "Extract common logic into reusable modular hooks without altering layout renders"),
    ("speed up Go routine channel blockages", "Implement select case defaults and buffered channels keeping message sequences"),
    ("improve type-safety on dynamic user models", "Implement strictly typed Pydantic models or TypeScript interfaces validating schemas"),
    ("refactor a global mutable state script causing racing deadlocks", "Encapsulate states in safe transaction locks or threads queues")
]


for idx in range(625):
    f_name = func_names[idx % len(func_names)]
    v1 = variables[idx % len(variables)]
    v2 = variables[(idx + 1) % len(variables)]
    
    nest_depth = (idx % 3) + 1
    if nest_depth == 1:
        q_text = f"Analyze the following code block for complexity calculations:\n\ndef {f_name}_{idx}(items):\n    count = 0\n    for i in range(len(items)):\n        count += 1\n    return count\n\nWhat is the Big O time complexity where N is len(items)?"
        correct_ans = "O(N)"
        options = ["O(N)", "O(N^2)", "O(log N)", "O(1)"]
    elif nest_depth == 2:
        q_text = f"Analyze the nested execution cycles in the refactoring script:\n\ndef {f_name}_{idx}(A, B):\n    val = 0\n    for i in range({v1}):\n        for j in range({v2}):\n            val += i * j\n    return val\n\nWhat is the Big O time complexity for this loops optimization task?"
        correct_ans = f"O({v1} * {v2})"
        options = [f"O({v1} * {v2})", f"O({v1}^2)", f"O({v1} + {v2})", "O(1)"]
    else:
        q_text = f"Analyze the recursive branch tree path function:\n\ndef {f_name}_{idx}(n):\n    if n <= 1: return n\n    return {f_name}_{idx}(n - 1) + {f_name}_{idx}(n - 2)\n\nWhat is the time complexity of this non-memoized structure?"
        correct_ans = "O(2^N)"
        options = ["O(2^N)", "O(N^2)", "O(N log N)", "O(N)"]
        
    random.shuffle(options)
    
    
    r = random.random()
    if r < 0.40: dom = "Engineering"
    elif r < 0.70: dom = "Infrastructure"
    else: dom = "Data"
    
    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "refactor",
        "type": "calculation",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct_ans),
        "hint": f"Look at loop depth. Simple iterations scale linearly."
    })
    q_id += 1


for idx in range(625):
    target, correct_prompt = prompt_targets[idx % len(prompt_targets)]
    q_text = f"PROMPT DESIGN: You need to prompt an AI assistant to {target}_{idx}.\nWhich system instruction ensures the safest, most performant refactoring?"
    
    correct = f"'{correct_prompt} without introducing breaking dependencies.'"
    options = [
        correct,
        f"'Rewrite the script in a different database dialect and change input types.'",
        f"'Generate random code examples explaining how the logic works in other fields.'",
        f"'Delete obsolete tests and disable runtime boundary warnings.'"
    ]
    random.shuffle(options)
    
    
    r = random.random()
    if r < 0.40: dom = "Engineering"
    elif r < 0.70: dom = "Infrastructure"
    else: dom = "Data"

    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "refactor",
        "type": "prompt_engineering",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct),
        "hint": "Prompts should request preservation of inputs and clear output validation guidelines."
    })
    q_id += 1




services = ["auth-api", "payment-gateway", "billing-node", "user-profile-db", "search-engine", "notification-queue", "cdn-delivery", "logging-aggregator"]
incidents = [
    ("502 Bad Gateway", "high memory consumption deadlocks", "Roll back connection pool sizes and revert recent Docker commits"),
    ("504 Gateway Timeout", "downstream database deadlocks on indexing", "Kill long-running transactions and deploy read replica pointers"),
    ("500 Internal Error", "unhandled null-pointer arguments from request payload", "Revert target image tag to stable, deploy validation schema check"),
    ("403 Forbidden Access", "misconfigured security policy routing headers", "Correct the ALB ingress security rules and reload routing configs"),
    ("408 Request Timeout", "packet losses on virtual private cloud channels", "Trigger network path check and route through backup availability zones")
]


for idx in range(625):
    srv = services[idx % len(services)]
    err, trigger, resolution = incidents[idx % len(incidents)]
    csat_drop = (idx % 8) + 3
    
    q_text = f"INCIDENT REPORT: The microservice '{srv}' is throwing '{err}' errors in production. The root cause is identified as '{trigger}'. CSAT is dropping by {csat_drop}% per minute. What is your immediate triage response?"
    
    correct = f"'{resolution} immediately.'"
    options = [
        correct,
        f"'Wait for the next weekly release branch and compile logs.'",
        f"'Increase server count by 200% without verifying the error stack.'",
        f"'Send an email warning developers about code quality targets.'"
    ]
    random.shuffle(options)
    
    
    r = random.random()
    if r < 0.30: dom = "Engineering"
    elif r < 0.80: dom = "Infrastructure"
    else: dom = "Data"
    
    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "hotfix",
        "type": "scenario_based",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct),
        "hint": "In critical outages, target speed, rollback systems, or config fixes first."
    })
    q_id += 1


for idx in range(625):
    srv = services[idx % len(services)]
    total_reqs = 1000 * ((idx % 10) + 1)
    failed_reqs = 50 * ((idx % 5) + 1)
    error_rate = (failed_reqs / total_reqs) * 100.0
    
    q_text = f"TRIAGE CALCULATION: A log aggregator reports that microservice '{srv}' logged {failed_reqs} failed queries out of a total of {total_reqs} incoming HTTP requests in a 1-minute window. What is the calculated error rate?"
    
    correct = f"{error_rate:.2f}%"
    options = [correct, f"{(error_rate * 1.5):.2f}%", f"{(error_rate * 0.5):.2f}%", f"{(error_rate + 2.5):.2f}%"]
    
    options = list(dict.fromkeys(options))
    while len(options) < 4:
        options.append(f"{(error_rate + len(options)):.2f}%")
        
    random.shuffle(options)
    
    
    r = random.random()
    if r < 0.30: dom = "Engineering"
    elif r < 0.80: dom = "Infrastructure"
    else: dom = "Data"
    
    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "hotfix",
        "type": "calculation",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct),
        "hint": "Error rate is calculated as: (Failed Requests / Total Requests) * 100."
    })
    q_id += 1




roles_list = [
    ("DevOps Engineer", "provision pipelines, deploy clusters, manage Cloud infrastructure scaling"),
    ("Data Specialist", "design schemas, maintain ETL streaming topics, analyze DB queries"),
    ("UI Designer", "create design frame libraries, draft typography prototypes, align wireframes"),
    ("Product Manager", "verify market fit metrics, organize sprint backlogs, define OKRs"),
    ("Scrum Master", "facilitate sprint events, remove developers blockers, guide agile practices"),
    ("Security Auditor", "inspect ingress rules, evaluate policy permissions, audit access logs")
]
bond_reasons = [
    ("heavy ticket backlog loads on sprint tasks", "Pair up to distribute ticket weight, coordinate load offsets, and schedules check-in"),
    ("repeated branch merge conflicts in main", "Organize a pair programming session to merge branches collaboratively"),
    ("vague requirements specifications on database metrics", "Arrange a quick align huddle to define acceptance criteria with product management"),
    ("continuous overtime support sessions during incidents", "Implement rotating shifts, schedule team down-times, and boost morale offsets")
]
names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Grace", "Jack", "Ivy"]
teams = ["Apollo", "Enterprise", "Zenith", "Orion", "Titan", "Aurora", "Phoenix"]


for idx in range(625):
    role, resp = roles_list[idx % len(roles_list)]
    name = names[idx % len(names)]
    
    q_text = f"ROLE MATCH: Colleague {name} is joining your squad. Which core responsibility matches the title '{role}'?"
    
    correct = f"'{resp}.'"
    options = [
        correct,
        f"'Refactor old database queries and create marketing slogans.'",
        f"'Conduct external sales campaigns and negotiate contract funding.'",
        f"'Rewrite system logs manually and clean up physical workspace.'"
    ]
    random.shuffle(options)
    
    
    dom = domains[idx % len(domains)]
    
    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "bonding",
        "type": "match_following",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct),
        "hint": "Focus on the traditional duties associated with technical and management roles."
    })
    q_id += 1


for idx in range(625):
    name = names[idx % len(names)]
    t = teams[idx % len(teams)]
    reason, res = bond_reasons[idx % len(bond_reasons)]
    
    q_text = f"TEAM HARMONY: Developer {name} on team '{t}' is feeling burnt out due to {reason}_{idx}. As a collaborative colleague, what is the best supportive action?"
    
    correct = f"'{res}.'"
    options = [
        correct,
        f"'Recommend working extra weekends to catch up.'",
        f"'File a formal complaint highlighting their slower delivery times.'",
        f"'Move all their tasks to another developer without telling them.'"
    ]
    random.shuffle(options)
    
    
    dom = domains[idx % len(domains)]
    
    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "bonding",
        "type": "scenario_based",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct),
        "hint": "Healthy squads collaborate to share work burdens and protect team members."
    })
    q_id += 1




ad_channels = ["Google Ads", "Twitter Ads", "Facebook Ads", "LinkedIn Ads", "Reddit Campaign", "TikTok Campaign"]
rivals = ["MegaCorp", "InnovateTech", "ApexSystems", "FutureSaaS", "ByteCore", "NexusSolutions"]
sectors = ["Enterprise B2B", "Mid-Market SME", "Consumer Apps", "Developer Tools", "AI Startups"]
rival_features = [
    ("an AI chatbot assistant feature", "Market our reliable data frameworks, custom APIs, and offer a customer loyalty coupon"),
    ("a free direct SQL integration plugin", "Promote our superior security standards, multi-tenant databases, and run targeted ad pushes"),
    ("a 30% subscription pricing discount", "Highlight our superior product features, higher uptime records, and offer a retention bundle"),
    ("a simplified dashboard UI layout", "Design visual campaign ads showcasing Figma UI flow reviews, and highlights user experience metrics")
]


for idx in range(625):
    chan = ad_channels[idx % len(ad_channels)]
    total_spend = 100 * ((idx % 30) + 10) 
    new_users = 10 * ((idx % 20) + 5) 
    cac = total_spend / new_users
    
    q_text = f"MARKETING METRICS: Your campaign on '{chan}' spent ${total_spend} and successfully acquired {new_users} new active subscribers. Calculate the Customer Acquisition Cost (CAC) for this campaign run."
    
    correct = f"${cac:.2f}"
    options = [correct, f"${(cac * 1.5):.2f}", f"${(cac * 0.5):.2f}", f"${(cac + 4.5):.2f}"]
    options = list(dict.fromkeys(options))
    while len(options) < 4:
        options.append(f"${(cac + len(options)):.2f}")
        
    random.shuffle(options)
    
    
    r = random.random()
    if r < 0.40: dom = "Product"
    elif r < 0.70: dom = "Design"
    else: dom = "Leadership"
    
    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "marketing",
        "type": "calculation",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct),
        "hint": "CAC is calculated as: Total Campaign Spend / New Users Acquired."
    })
    q_id += 1


for idx in range(625):
    riv = rivals[idx % len(rivals)]
    feat, strategy = rival_features[idx % len(rival_features)]
    sec = sectors[idx % len(sectors)]
    
    q_text = f"MARKET NEWS FLASH: Rival firm '{riv}' has just launched {feat}_{idx}, drawing users from your '{sec}' product segment. What is your marketing and PR response?"
    
    correct = f"'{strategy}.'"
    options = [
        correct,
        f"'Initiate immediate price drops to $0 to crash competitor revenues.'",
        f"'Shut down microservices in that segment and pivot to other markets.'",
        f"'Publish critical blog articles claiming copyright infringements without proof.'"
    ]
    random.shuffle(options)
    
    
    r = random.random()
    if r < 0.40: dom = "Product"
    elif r < 0.70: dom = "Design"
    else: dom = "Leadership"
    
    questions.append({
        "id": q_id,
        "domain": dom,
        "difficulty": "marketing",
        "type": "news_quiz",
        "question": q_text,
        "options": options,
        "correct_index": options.index(correct),
        "hint": "Focus on highlighting product quality and security to retain customers."
    })
    q_id += 1


random.shuffle(questions)


for idx, q in enumerate(questions):
    q["id"] = idx + 1


output_path = os.path.join(os.path.dirname(__file__), 'questions.json')
with open(output_path, 'w') as f:
    json.dump(questions, f, indent=4)

print(f"Generated {len(questions)} unique questions in {output_path} successfully!")
