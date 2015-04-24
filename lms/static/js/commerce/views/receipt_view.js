/**
 * View for the receipt page.
 */
var edx = edx || {};

(function ($, _, Backbone, gettext) {
    'use strict';

    edx.commerce = edx.commerce || {};

    edx.commerce.ReceiptView = edx.verify_student.PaymentConfirmationStepView.extend({

        defaultContext: function () {
            var context = edx.commerce.ReceiptView.__super__.defaultContext.apply(this);
            context['platformName'] = this.$el.data('platform-name');
            return context;
        },

        initialize: function (obj) {
            edx.commerce.ReceiptView.__super__.initialize.apply(this, obj);
            this.templateName = 'receipt';
        },

        /**
         * Retrieve receipt data from Oscar (via LMS).
         * @param  {int} basketId The basket that was purchased.
         * @return {object}                 JQuery Promise.
         */
        getReceiptData: function (basketId) {
            return $.ajax({
                url: _.sprintf('/commerce/baskets/%s/order/', basketId),
                type: 'GET',
                dataType: 'json'
            }).retry({times: 3, timeout: 2000, statusCodes: [404]});
        },

        /**
         * Construct the template context from data received
         * from the shopping cart receipt.
         *
         * @param  {object} order Receipt data received from the server
         * @return {object}      Receipt template context.
         */
        receiptContext: function (order) {
            var view = this,
                receiptContext;

            receiptContext = {
                orderNum: order.number,
                currency: order.currency,
                purchasedDatetime: order.date_placed,
                totalCost: view.formatMoney(order.total_excl_tax),
                isRefunded: false,
                billedTo: {
                    firstName: order.billing_address.first_name,
                    lastName: order.billing_address.last_name,
                    city: order.billing_address.city,
                    state: order.billing_address.state,
                    postalCode: order.billing_address.postcode,
                    country: order.billing_address.country
                },
                items: []
            };

            receiptContext.items = _.map(
                order.lines,
                function (line) {
                    return {
                        lineDescription: line.description,
                        cost: view.formatMoney(line.line_price_excl_tax)
                    };
                }
            );

            return receiptContext;
        },

        getOrderCourseKey: function (order) {
            var length = order.lines.length;
            for (var i = 0; i < length; i++) {
                var line = order.lines[i],
                    attribute_values = _.filter(line.product.attribute_values, function (attribute) {
                        return attribute.name == 'course_key'
                    });

                if (attribute_values.length > 0) {
                    return attribute_values[0]['value'];
                }
            }

            return null;
        },

        updateContext: function (templateContext) {
            var view = this;
            return $.Deferred(
                function (defer) {
                    var paymentOrderNum = $.url('?basket_id');
                    if (paymentOrderNum) {
                        // If there is a payment order number, try to retrieve
                        // the receipt information from the shopping cart.
                        view.getReceiptData(paymentOrderNum).then(
                            function (data) {
                                // Add the receipt info to the template context
                                _.extend(templateContext, {
                                    receipt: this.receiptContext(data),
                                    courseKey: this.getOrderCourseKey(data)
                                });
                                defer.resolveWith(view, [templateContext]);
                            }
                            , function () {
                                // Display an error
                                // This can occur if the user does not have access to the receipt
                                // or the order number is invalid.
                                defer.rejectWith(
                                    this,
                                    [
                                        gettext("Error"),
                                        gettext("Could not retrieve payment information")
                                    ]
                                );
                            });
                    } else {
                        // If no payment order is provided, return the original context
                        // The template is responsible for displaying a default state.
                        _.extend(templateContext, {receipt: null});
                        defer.resolveWith(view, [templateContext]);
                    }
                }
            ).promise();
        }
    });

    new edx.commerce.ReceiptView({
        el: $('#pay-and-verify-container')
    }).render();
})(jQuery, _, Backbone, gettext);
