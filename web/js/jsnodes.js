const { app } = window.comfyAPI.app;

app.registerExtension({
    name: "OPM_openpose_manager",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (!["OPM_SkeletonFromIDs", "SkeletonFromJSON"].includes(nodeData.name)) {
            return;
        }

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated || function () {};
        nodeType.prototype.onNodeCreated = function () {
            originalOnNodeCreated.apply(this, arguments);

            this.addWidget("button", "Update inputs", null, () => {
                if (!this.inputs) {
                    this.inputs = [];
                }

                const target_number_of_inputs = this.widgets.find(w => w.name === "num_people")?.value || 1;
                const num_inputs = this.inputs.filter(input => input.name && input.name.toLowerCase().startsWith("pose_")).length;
                if (target_number_of_inputs === num_inputs) {
                    return;
                }

                if (target_number_of_inputs < num_inputs) {
                    const inputs_to_remove = num_inputs - target_number_of_inputs;
                    for (let i = 0; i < inputs_to_remove; i++) {
                        this.removeInput(this.inputs.length - 1);
                    }
                } else {
                    for (let i = num_inputs + 1; i <= target_number_of_inputs; ++i) {
                        this.addInput(`pose_${i}_id`, "INT", { shape: 7 });
                    }
                }
            });

            const initial_number_of_inputs = this.widgets.find(w => w.name === "num_people")?.value || 1;
            const existing_inputs = this.inputs.filter(input => input.name && input.name.toLowerCase().startsWith("pose_")).length;
            for (let i = existing_inputs + 1; i <= initial_number_of_inputs; ++i) {
                this.addInput(`pose_${i}_id`, "INT", { shape: 7 });
            }
        };
    }
});
