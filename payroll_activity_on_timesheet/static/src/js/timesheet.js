odoo.define('hr_timesheet_sheet.sheet', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Model = require('web.DataModel');
var time = require('web.time');
var utils = require('web.utils');

var QWeb = core.qweb;
var _t = core._t;

var WeeklyTimesheet = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
    events: {
        "click .oe_timesheet_weekly_account a": "go_to",
    },
    ignore_fields: function() {
        return ['line_id'];
    },
    init: function() {
        this.account_names = {};
        this.activity_names = {};

        this._super.apply(this, arguments);
        this.set({
            sheets: [],
            date_from: false,
            date_to: false,
        });

        this.field_manager.on("field_changed:timesheet_ids", this, this.query_sheets);
        this.field_manager.on("field_changed:date_from", this, function() {
            this.set({"date_from": time.str_to_date(this.field_manager.get_field_value("date_from"))});
        });
        this.field_manager.on("field_changed:date_to", this, function() {
            this.set({"date_to": time.str_to_date(this.field_manager.get_field_value("date_to"))});
        });
        this.field_manager.on("field_changed:user_id", this, function() {
            this.set({"user_id": this.field_manager.get_field_value("user_id")});
        });
        this.on("change:sheets", this, this.update_sheets);
        this.res_o2m_drop = new utils.DropMisordered();
        this.render_drop = new utils.DropMisordered();
        this.description_line = _t("/");
    },
    go_to: function(event) {
        var id = JSON.parse($(event.target).data("id"));
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "account.analytic.account",
            res_id: id,
            views: [[false, 'form']],
        });
    },
    query_sheets: function() {
        if (this.updating) {
            return;
        }

        var commands = this.field_manager.get_field_value("timesheet_ids");
        var self = this;
        this.res_o2m_drop.add(new Model(this.view.model).call("resolve_2many_commands", 
                ["timesheet_ids", commands, [], new data.CompoundContext()]))
            .done(function(result) {
                self.querying = true;
                self.set({sheets: result});
                self.querying = false;
            });
    },
    update_sheets: function() {
        if(this.querying) {
            return;
        }
        this.updating = true;

        var commands = [form_common.commands.delete_all()];
        _.each(this.get("sheets"), function (_data) {
            var data = _.clone(_data);
            if(data.id) {
                commands.push(form_common.commands.link_to(data.id));
                commands.push(form_common.commands.update(data.id, data));
            } else {
                commands.push(form_common.commands.create(data));
            }
        });

        var self = this;
        this.field_manager.set_values({'timesheet_ids': commands}).done(function() {
            self.updating = false;
        });
    },
    initialize_field: function() {
        form_common.ReinitializeWidgetMixin.initialize_field.call(this);
        this.on("change:sheets", this, this.initialize_content);
        this.on("change:date_to", this, this.initialize_content);
        this.on("change:date_from", this, this.initialize_content);
        this.on("change:user_id", this, this.initialize_content);
    },
    map_accounts: function(self, accounts, dates, default_get) {
        // for each account in the dict we map the account defaults
        // this is required so that the timesheet receives the correct analytic journal
        return _(accounts).chain().map(function(activities, account_id){
            var accounts_defaults = _.extend({}, default_get,
                (accounts[account_id] || {}).value || {}
            );

            // map days in activities
            var activities = self.map_activities(self, activities, account_id, dates, accounts_defaults);

            // sort activities by name
            activities = _.sortBy(activities, function(activity){
                return self.activity_names[activity.activity_id];
            });

            return {
                account_id: account_id,
                activities: activities,
                accounts_defaults: accounts_defaults,
            };
        }).value();
    },
    map_activities: function(self, activities, account_id, dates, accounts_defaults){
        // for each activity map the timesheet lines into days (list of timesheets)
        // the first element in days must be the record where we will insert/remove time
        return _(activities).chain().map(function(lines, activity_id){
            activity_id = activity_id === "false" ? false :  Number(activity_id);
            var index = _.groupBy(lines, "date");
            var days = _.map(dates,function(date){
                var day = {
                    day: date,
                    lines: index[time.date_to_str(date)] || []
                };
                // add a timesheet record where we will insert/remove hours
                var to_add = _.find(day.lines, function(line){
                    return line.name === self.description_line;
                });
                if (to_add){
                    // find the record where we insert/remove
                    // place it at the beginning of the list of records
                    day.lines = _.without(day.lines, to_add);
                    day.lines.unshift(to_add);
                }
                else{
                    // if cant find the record, create one and
                    // place it at the beginning of the record list
                    day.lines.unshift(_.extend(_.clone(accounts_defaults), {
                        name: self.description_line,
                        unit_amount: 0,
                        date: time.date_to_str(date),
                        account_id: account_id,
                        activity_id: activity_id,
                    }));
                }
                return day;
            });
            return {
                days: days,
                activity_id: activity_id,
            };
        }).value();
    },
    initialize_content: function() {
        if(this.setting) {
            return;
        }

        // don't render anything until we have date_to and date_from
        if (!this.get("date_to") || !this.get("date_from")) {
            return;
        }

        // it's important to use those vars to avoid race conditions
        var dates;
        var accounts;
        var default_get;
        var self = this;
        return this.render_drop.add(new Model("account.analytic.line").call("default_get", [
            [
                'account_id',
                'general_account_id',
                'journal_id',
                'date',
                'name',
                'user_id',
                'product_id',
                'product_uom_id',
                'amount',
                'unit_amount',
                'is_timesheet',
            ], new data.CompoundContext({'user_id': self.get('user_id'), 'default_is_timesheet': true})
        ]).then(function(result) {
            default_get = result;
            // calculating dates
            dates = [];
            var start = self.get("date_from");
            var end = self.get("date_to");
            while (start <= end) {
                dates.push(start);
                var m_start = moment(start).add(1, 'days');
                start = m_start.toDate();
            }
            // group by account
            var activity_ids = [];
            var account_ids = [];

            accounts = _(self.get("sheets")).chain().map(function(el){
                if (typeof(el.account_id) === "object"){
                    // add account id to list of accounts
                    el.account_id = el.account_id[0];
                    account_ids.push(el.account_id);
                }
                if (typeof(el.activity_id) === "object"){
                    // add activity id to list of activities
                    el.activity_id = el.activity_id[0];
                    activity_ids.push(el.activity_id);
                }
                return el;
            }).groupBy('account_id').value();

            // for each value of the dict, create a dict mapped by activity that contains the timesheet records
            accounts = _.each(accounts, function(account, key){
                accounts[key] = _.groupBy(account, 'activity_id');
            });

            account_ids = _.uniq(account_ids);
            activity_ids = _.uniq(activity_ids);

            // We need the name of the activities and account to be displayed
            var deferred_1 = self.get_activity_names(self, activity_ids);
            var deferred_2 = self.get_account_names(self, account_ids);

            $.when(deferred_1, deferred_2).done(function(){

                // modify the account dict so that it can be parsed to fill the timesheet
                accounts = self.map_accounts(self, accounts, dates, default_get);
                // sort the accounts by name
                accounts = _.sortBy(accounts, function(account){
                    return self.account_names[account.account_id];
                });

                self.dates = dates;
                self.accounts = accounts;
                self.default_get = default_get;

                // fill the timesheet
                self.display_data();
            });
        }));
    },
    get_account_names: function(self, account_ids){
        // we want only the records that are not in the current dict of names
        account_ids = _.filter(account_ids, function(account){
            return !(account in self.account_names);
        });
        // we make a querry only if there is at least one unknowed value
        if(account_ids.length !== 0){
            var defered = new Model("account.analytic.account").call(
                "name_get", [account_ids, new data.CompoundContext()]
            ).then(function(result){
                // name_get returns a list of tuples (id, name), we need a dict
                var account_names = {};
                _.each(result, function(el){
                    account_names[el[0]] = el[1];
                });
                // update the current dict of names
                self.account_names = _.extend(self.account_names, account_names);
            });
            return defered;
        }
    },
    get_activity_names: function(self, activity_ids){
        // we want only the records that are not in the current dict of names
        activity_ids = _.filter(activity_ids, function(activity){
            return !(activity in self.activity_names);
        });
        // we make a querry only if there is at least one unknowed value
        if(activity_ids.length !== 0){
            var defered = new Model("hr.activity").call(
                "name_get", [activity_ids, new data.CompoundContext()]
            ).then(function(result){
                // name_get returns a list of tuples (id, name), we need a dict
                var activity_names = {};
                _.each(result,function(el){
                    activity_names[el[0]] = el[1];
                });
                // update the current dict of names
                self.activity_names = _.extend(self.activity_names, activity_names);
            });
            return defered;
        }
    },
    destroy_content: function() {
        if (this.dfm) {
            this.dfm.destroy();
            this.dfm = undefined;
        }
    },
    is_valid_value:function(value){
        var split_value = value.split(":");
        var valid_value = true;
        if (split_value.length > 2) {
            return false;
        }
        _.detect(split_value,function(num){
            if(isNaN(num)) {
                valid_value = false;
            }
        });
        return valid_value;
    },
    display_data: function(){
        var self = this;
        self.$el.html(QWeb.render("payroll_activity_on_timesheet.WeeklyTimesheet", {widget: self}));
        // Accounts contain activities, Activities contain days, days contain amounts
        // sort accounts and activities by name
        _.each(self.accounts, function(account){
            _.each(account.activities, function(activity){
                _.each(_.range(activity.days.length), function(day_count){
                    if (!self.get('effective_readonly')){
                        // get the amount in the related text input
                        self.get_box(account, activity, day_count).val(self.sum_box(activity, day_count, true)).change(function(){
                            var num = $(this).val();
                            //check if new input value is numeric
                            if (self.is_valid_value(num)){
                                num = (num === 0) ? 0: Number(self.parse_client(num));
                            }
                            //check if new input value is legal numeric
                            if (isNaN(num)){
                                $(this).val(self.sum_box(activity, day_count, true));
                            }
                            else{
                                activity.days[day_count].lines[0].unit_amount += num - self.sum_box(activity, day_count);

                                if(!isNaN($(this).val())){
                                    $(this).val(self.sum_box(activity, day_count, true));
                                }

                                self.display_totals();
                                self.sync();
                            }
                        });
                    }
                    else{
                        self.get_box(account, activity, day_count).html(self.sum_box(activity, day_count, true));
                    }
                });
            });
        });
        self.display_totals();
        self.$(".oe_timesheet_button_add").click(_.bind(this.init_add_account, this));
        this.close_account_selector();
    },
    // Method to manage the account/activity selector
    init_add_account: function() {
        var self = this;
        if (self.dfm)
            return;
        // create the 'Next' button
        self.$(".oe_timesheet_weekly_select_account_activity").show();
        self.$(".oe_timesheet_weekly_add_row").show();
        self.$(".oe_timesheet_weekly_adding").hide();
        self.$(".oe_timesheet_weekly_cancel").show();

        // create the inputs to select the account and the activity
        this.dfm = new form_common.DefaultFieldManager(this);
        self.dfm.extend_field_desc({
            account: {relation: "account.analytic.account"},
            activity: {relation: "hr.activity"},
        });

        var FieldMany2One = core.form_widget_registry.get('many2one');

        self.account_m2o = new FieldMany2One(self.dfm, {
            attrs: {
                name: "account",
                type: "many2one",
                modifiers: '{"required": true}',
                domain: [['account_type', '=', 'normal']],
            },
        });

        // Set default value of the analytic account field
        self.account_m2o.get_search_result('').then(function(data){
            if (data.length > 0){
                self.account_m2o.set_value(data[0]['id']);
            }
        });

        // create the input to select the activity
        self.activity_m2o = new FieldMany2One(self.dfm, {
            attrs: {
                name: "activity",
                type: "many2one",
                domain: [['authorized_user_ids', '=', self.get('user_id')], ['authorized_user_ids', '!=', false]],
                context: new data.CompoundContext({user_id: self.get('user_id')}),
                modifiers: '{"required": true}',
            },
        });

        // When the account is changed, need to change the context of the activity field.
        // If the current selected activity is not autorized for the selected account,
        // replace the activity selected with the first value in the list of authorized activities.
        self.account_m2o.on('changed_value', this, function() {
            var node = self.activity_m2o.node;
            node.attrs.context = new data.CompoundContext(
                node.attrs.context, {
                    user_id: self.get('user_id'),
                    account_id: self.account_m2o.get_value(),
                }
            );
            var activity_field = self.activity_m2o;

            // Search activities
            self.activity_m2o.get_search_result('').then(function(data){
                var previous_activity_id = self.activity_m2o.get_value();
                var activity_dict = _.indexBy(data, 'id');

                if (! (previous_activity_id in activity_dict)){
                    if (data.length > 0 ){
                        self.activity_m2o.set_value(data[0]['id']);
                    }
                    else {
                        self.activity_m2o.set_value(false);
                    }
                }
            });
        });

        // Place the fields in the widget
        self.activity_m2o.prependTo(this.$(".oe_timesheet_activity_many2one")).then(function() {
            self.activity_m2o.$el.addClass('oe_edit_only');
        })
        this.account_m2o.prependTo(this.$(".oe_timesheet_account_many2one")).then(function() {
            self.account_m2o.$el.addClass('oe_edit_only');
        })

        self.$(".oe_timesheet_weekly_cancel").click(function(){
            self.set({"sheets": self.generate_o2m_value()});
            self.close_account_selector();
            self.destroy_content();
        });

        self.$(".oe_timesheet_weekly_add_row button").click(function(){
            var activity_id = self.activity_m2o.get_value();
            var account_id = self.account_m2o.get_value();
            if (account_id === false) {
                self.dfm.set({display_invalid_fields: true});
                return;
            }
            if(self.activity_m2o.get_value() === false){
                self.dfm.set({display_invalid_fields: true});
                return;
            }

            // Update the dicts of names with the selected account and activities
            var deferred_1 = self.get_account_names(self, [account_id]);
            var deferred_2 = self.get_activity_names(self, [activity_id]);

            $.when(deferred_1, deferred_2).done(function(){
                self.close_account_selector();
                var ops = self.generate_o2m_value();
                var new_timesheet_line = _.extend({}, self.default_get, {
                    name: self.description_line,
                    unit_amount: 0,
                    date: time.date_to_str(self.dates[0]),
                    account_id: account_id,
                    activity_id: activity_id,
                });
                ops.push(new_timesheet_line);
                self.set({"sheets": ops});
                self.destroy_content();
            });
        });
    },
    close_account_selector: function() {
        self.$(".oe_timesheet_weekly_select_account_activity").hide();
        self.$(".oe_timesheet_weekly_add_row").hide();
        self.$(".oe_timesheet_weekly_adding").show();
        self.$(".oe_timesheet_weekly_cancel").hide();
    },
    get_box: function(account, activity, day_count){
        return this.$(
            '[data-account="'.concat(account.account_id, '"][data-activity="', activity.activity_id, '"][data-day-count="', day_count, '"]')
        );
    },
    get_total: function(account, activity) {
        return this.$('[data-account-total="' + account.account_id + '"][data-activity-total="' + activity.activity_id + '"]');
    },
    get_day_total: function(day_count) {
        return this.$('[data-day-total="' + day_count + '"]');
    },
    get_super_total: function() {
        return this.$('.oe_timesheet_weekly_supertotal');
    },
    sum_box: function(account, day_count, show_value_in_hour) {
        var line_total = 0;
        _.each(account.days[day_count].lines, function(line) {
            line_total += line.unit_amount;
        });
        return (show_value_in_hour && line_total != 0) ? this.format_client(line_total) : line_total;
    },
    display_totals: function() {
        var self = this;
        var day_tots = _.map(_.range(self.dates.length), function() { return 0; });
        var super_tot = 0;
        _.each(self.accounts, function(account) {
            _.each(account.activities, function(activity){
                var acc_tot = 0;
                _.each(_.range(self.dates.length), function(day_count) {
                    var sum = self.sum_box(activity, day_count);
                    acc_tot += sum;
                    day_tots[day_count] += sum;
                    super_tot += sum;
                });
                self.get_total(account, activity).html(self.format_client(acc_tot));
            });
        });
        _.each(_.range(self.dates.length), function(day_count) {
            self.get_day_total(day_count).html(self.format_client(day_tots[day_count]));
        });
        self.get_super_total().html(self.format_client(super_tot));
    },
    sync: function() {
        this.setting = true;
        this.set({sheets: this.generate_o2m_value()});
        this.setting = false;
    },
    //converts hour value to float
    parse_client: function(value) {
        return formats.parse_value(value, { type:"float_time" });
    },
    //converts float value to hour
    format_client:function(value){
        return formats.format_value(value, { type:"float_time" });
    },
    generate_o2m_value: function() {
        var self = this;
        var ops = [];
        var ignored_fields = self.ignore_fields();
        _.each(self.accounts, function(account) {
            _.each(account.activities, function(activity){
                _.each(activity.days, function(day) {
                    _.each(day.lines, function(line) {
                        if (line.unit_amount !== 0) {
                            var tmp = _.clone(line);
                            tmp.id = undefined;
                            _.each(line, function(v, k) {
                                if (v instanceof Array) {
                                    tmp[k] = v[0];
                                }
                            });
                            // we remove line_id as the reference to the _inherits field will no longer exists
                            tmp = _.omit(tmp, ignored_fields);
                            ops.push(tmp);
                        }
                    });
                });
            });
        });
        return ops;
    },
});

core.form_custom_registry.add('weekly_timesheet', WeeklyTimesheet);

});
