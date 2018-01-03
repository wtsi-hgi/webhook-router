<template>
<div>
    <whr-navbar>
        <router-link to="/">
            <button type="button" class="btn btn-outline-secondary">
                <span class="oi oi-chevron-left"></span> Back
            </button>
        </router-link>
    </whr-navbar>
    <slot name="errors"></slot>
    <div v-show="loaded" class="container">
        <br />
        <h1>
            Admin Panel
        </h1>
        <hr>
        <h2>Firewall rules</h2>
        <hr>
            <p>
                List rules of allowed routes, used to display a warning to users when they enter an invalid route.
            </p>
        <table class="table">
            <thead>
                <tr>
                    <th>
                        CIDR
                    </th>
                    <th>
                        <span data-toggle="tooltip" title="Range or specific port to allow e.g. 80-100 or 80">Ports</span>
                    </th>
                    <th v-html="'&nbsp;'">
                    </th>
                </tr>
            </thead>
            <tbody>
                <br />
                <tr v-for="(rule, index) in rules">
                    <td>
                        <input class="form-control"
                        required
                        pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                        type="text" v-model="rule.cidr"/>
                    </td>
                    <td>
                        <input class="form-control" type="text" v-model="rule.ports" placeholder="e.g. 80-100 or 80"/>
                    </td>
                    <td style="vertical-align: middle;">
                        <span @click="removeRule(index)" class="oi oi-x"></span>
                    </td>
                </tr>
                <button style="margin-left: 12px" @click="addRule" class="btn btn-sm btn-outline-secondary">
                    <span class="oi oi-plus"></span> Add Rule
                </button>
            </tbody>
        </table>
        <br />
        <h2>
            Admin users
        </h2>
        <hr>
        <ul class="list-unstyled">
            <li v-for="(user, index) in adminUsers" :key="user" style="vertical-align: middle;padding-top: 10px;">
                <span class="col-11" style="display: inline-block">
                    <input class="form-control" style="display: inline-block" type="text" v-model="adminUsers[index]"/>
                    <br />
                </span>
                <span class="col-1">
                    <span @click="removeAdminUser(index)" class="oi oi-x"></span>
                </span>
            </li>
        </ul>
        <button @click="addAdminUser" style="margin-left:15px" class="btn btn-sm btn-outline-secondary">
            <span class="oi oi-plus"></span> Add Admin User
        </button>
        <br />
        <hr>
        <button @click="saveChanges" class="btn btn-outline-success">
            Save Changes
        </button>
        <br />
        <br />
    </div>
</div>
</template>
<script lang="ts">
import Vue from "vue";
import Component from 'vue-class-component';
import NavBarComponent from "./whr-navbar.vue";
import { Prop } from 'vue-property-decorator';

interface Rule{
    cidr: string;
    ports: string;
}

@Component({
    components: {
        "whr-navbar": NavBarComponent
    }
})
export default class AdminPanel extends Vue {
    @Prop() adminAPI: SwaggerAPI<BasicAPI>;
    loaded = false;

    rules: Rule[] = [{
        cidr: "127.0.0.1/16",
        ports: "80-1000"
    }];

    adminUsers: string[] = [
        "th10@sanger.ac.uk",
        "cn13@sanger.ac.uk"
    ]

    addRule(){
        this.rules.push({
            cidr: "",
            ports: ""
        })
    }

    async saveChanges(){
        let newRules = this.rules.map(rule => {
            let from_port: number, to_port: number;

            let portsStrParts = rule.ports.split("-");
            if(portsStrParts.length == 1){
                from_port = to_port = parseInt(portsStrParts[0]);
            }
            else if(portsStrParts.length == 2){
                [from_port, to_port] = portsStrParts.map(x => parseInt(x));
            }
            else{
                throw Error(`Cannot save firewall rules, port definiton ${rule.ports} is invalid`);
            }

            if([from_port, to_port].some(x => isNaN(x))){
                throw Error(`Cannot save firewall rules, port definiton ${rule.ports} is invalid`);
            }

            if(!rule.cidr){
                throw Error("CIDR need to be defined");
            }

            return {
                from_port,
                to_port,
                cidr: rule.cidr
            }
        })

        let jsonDocument = {
            firewallRules: newRules,
            adminUsers: this.adminUsers
        }

        await this.adminAPI.apis.default.set_config({
            new_config: jsonDocument
        })
    }

    removeRule(index: number){
        this.rules.splice(index, 1);
    }

    addAdminUser(){
        this.adminUsers.push("");
    }

    removeAdminUser(index: number){
        this.adminUsers.splice(index, 1);
    }

    async mounted(){
        $('[data-toggle="tooltip"]').tooltip();

        let configJSON = (await this.adminAPI.apis.default.get_config()).obj;
        this.rules = configJSON.firewallRules.map(rule => ({
            ports: rule.from_port == rule.to_port? rule.from_port : `${rule.from_port}-${rule.to_port}`,
            cidr: rule.cidr
        }));
        this.adminUsers = configJSON.adminUsers;

        this.loaded = true;
    }
}
</script>

