import os
import subprocess
import json
from datetime import datetime
from app.models.domain import Execution, ExecutionResult
from app import db

class NativeRunner:
    def run_spec(self, project, scenario, filepath: str) -> int:
        """
        Executes the specific generated spec file using the project's native command.
        Parses JSON output and saves to the database.
        Returns Execution.id
        """
        # Create execution record
        exec_record = Execution(
            project_id=project.id,
            target_url=project.target_directory, # Used to denote target context
            engine='native_cli',
            mode='Enterprise'
        )
        db.session.add(exec_record)
        db.session.commit()
        
        # We need the relative path for the test runner if they are in the directory
        rel_filepath = os.path.relpath(filepath, project.target_directory)
        
        cmd = f"{project.test_command} {rel_filepath}"
        
        start_time = datetime.utcnow()
        try:
            # We expect the test_command to include --reporter=json
            # Playwright outputs json to stdout if --reporter=json is used
            # But it can also include extra stdout. We should probably capture it and parse carefully.
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=project.target_directory,
                capture_output=True,
                text=True
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Parse JSON output from Playwright
            # The output might have other text before/after the JSON.
            # Try to find the JSON block. It usually starts with { and contains "config", "suites"
            parsed_json = None
            try:
                # Naive json extraction
                json_str = result.stdout[result.stdout.find('{'):result.stdout.rfind('}')+1]
                parsed_json = json.loads(json_str)
            except Exception as e:
                print(f"Failed to parse Playwright JSON reporter output: {e}")
                
            status = 'Failed'
            error_msg = result.stderr or result.stdout
            
            if parsed_json and 'errors' in parsed_json:
                if len(parsed_json['errors']) == 0:
                    status = 'Passed'
                    error_msg = None
                else:
                    status = 'Failed'
                    error_msg = str(parsed_json['errors'])
            elif result.returncode == 0:
                status = 'Passed'
                error_msg = None
                
            # Create Execution Result
            exec_result = ExecutionResult(
                execution_id=exec_record.id,
                scenario_id=scenario.id,
                status=status,
                duration=duration,
                error_message=error_msg
            )
            db.session.add(exec_result)
            
            exec_record.status = 'Completed' if status == 'Passed' else 'Failed'
            exec_record.end_time = end_time
            exec_record.duration = duration
            
            db.session.commit()
            
            return exec_record.id
            
        except Exception as e:
            end_time = datetime.utcnow()
            exec_result = ExecutionResult(
                execution_id=exec_record.id,
                scenario_id=scenario.id,
                status='Failed',
                duration=(end_time - start_time).total_seconds(),
                error_message=f"System Error: {str(e)}"
            )
            db.session.add(exec_result)
            
            exec_record.status = 'Failed'
            exec_record.end_time = end_time
            db.session.commit()
            
            return exec_record.id

native_runner = NativeRunner()
