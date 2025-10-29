# contracts/serializers.py
from rest_framework import serializers
from .models import Contract

class ContractSerializer(serializers.ModelSerializer):
    """
    Serializer for the Contract model.
    """
    # Provide the company name for easy display in lists.
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Contract
        fields = [
            'id', 'company', 'company_name', 'start_date', 'end_date', 
            'status', 'notes', 'created_at'
        ]
        # Make the company field write-only, as company_name is used for reading.
        extra_kwargs = {
            'company': {'write_only': True}
        }

    def validate(self, data):
        """
        Custom validation to check if start_date is before end_date.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("The contract end date cannot be before the start date.")
        
        return data