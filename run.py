# run.py
from app import create_app, db
from flask_migrate import Migrate
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = create_app()
migrate = Migrate(app, db)

@app.route('/debug')
def debug_route():
    return 'Debug route works!'

if __name__ == '__main__':
    print("\n=== Final Registered Routes ===")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    print("========================\n")
    
    print("\n=== Final Registered Blueprints ===")
    for name, blueprint in app.blueprints.items():
        bp_prefix = blueprint.url_prefix or "None"
        print(f"Blueprint: {name}, URL Prefix: {bp_prefix}")
    print("========================\n")
    
    app.run(debug=True)