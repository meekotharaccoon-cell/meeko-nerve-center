class AgenticCRM:
    def deploy_for_role(self, role, user_id):
        swarm = self.role_swarms[role]
        context = self.stateful_memory.get_user_context(user_id)
        return swarm.personalize(context)
