from agent_smithers.github import GitHubClient, GitHubClientConfig

client = GitHubClient(config=GitHubClientConfig(organization="orkestra-energy"))

repos = client.search_code_in_repository("vippy_backend", "vp.Bill")
print(repos)
