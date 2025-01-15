from typing import Dict, List
import asyncio
import docker
import os
import subprocess

class AnalyzerManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.analyzers = {}
        
    async def initialize_analyzers(self):
        """Start all analyzer containers if not running"""
        compose_file = os.path.join(os.path.dirname(__file__), 'docker-compose.yml')
        
        try:
            subprocess.run(
                ['docker-compose', '-f', compose_file, 'up', '-d'],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise AnalyzerInitializationError(f"Failed to start analyzers: {str(e)}")
    
    async def run_analysis(self, source_path: str) -> Dict[str, List]:
        """Run all analyzers in parallel"""
        tasks = []
        for analyzer in self.analyzers.values():
            tasks.append(analyzer.execute(source_path))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and format results
        return self._combine_results(results)
    
    async def cleanup(self):
        """Stop and remove analyzer containers"""
        compose_file = os.path.join(os.path.dirname(__file__), 'docker-compose.yml')
        subprocess.run(
            ['docker-compose', '-f', compose_file, 'down'],
            check=True
        )