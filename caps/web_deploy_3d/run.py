"""web_deploy_3d -- GBT 3D 网页部署能力"""
from caps.web_deploy_3d import get_design_context, manifest

HANDLERS = {
    "get_design_context": get_design_context,
    "manifest": manifest,
}

if __name__ == "__main__":
    print(get_design_context())